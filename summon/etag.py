# SPDX-License-Identifier: BSD-3-Clause
from flask import request, make_response, jsonify, Response
from typing import Any, TypeAlias
from collections.abc import Callable
from hashlib import sha256

__all__ = (
	'ETagCache',
)

JSONHandler: TypeAlias = Callable[[], dict[str, Any] | list[Any]]

# Defines a cache which uses ETags of the content to determine whether to spend bandwidth or not
class ETagCache:
	def __init__(self) -> None:
		self.etagCache: dict[Callable, str] = {}
		self.responseCache: dict[Callable, Response] = {}

	# Decorates an endpoint that returns JSON for being ETag cached
	def json(self, handler: JSONHandler):
		return ETagJSONHandler(self, handler)

	# Look up a handler to see if there's an etag in cache for it
	def lookupETag(self, handler) -> str | None:
		return self.etagCache.get(handler)

	# Look up a handler to see if there's a response in cache for it
	def lookupResponse(self, handler) -> Response | None:
		return self.responseCache.get(handler)

	# Cache a response, computing its etag
	def etag(self, handler, response: Response):
		etag = f'"{sha256(response.data).hexdigest()}"'
		response.headers["ETag"] = etag

		# Enter the new ETag and response into the cache
		self.etagCache[handler] = etag
		self.responseCache[handler] = response

# Defines the handling for an ETag cached request for JSON
class ETagJSONHandler:
	def __init__(self, cache: ETagCache, handler: JSONHandler):
		self.cache = cache
		self.handler = handler

	# Invoked when this handler is called on for a request
	def __call__(self):
		# Check to see if the request has an If-None-Match ETag header
		etag = request.headers.get('If-None-Match')
		# If the request does, look the handler up in the ETag cache and check if they match
		if etag is not None:
			cachedETag = self.cache.lookupETag(self.handler)
			# If the tags match, tell the client nothing changed
			if cachedETag == etag:
				response = make_response('Not Modified', 304)
				response.headers['ETag'] = etag
				return response

		# If we didn't get a matching ETag from the client, see if there's a cached response
		response = self.cache.lookupResponse(self.handler)
		# If there is, then we're done - just return it.
		if response is not None:
			return response

		# Otherwise, we have to build a new one
		response = jsonify(self.handler())
		self.cache.etag(self.handler, response)
		return response
