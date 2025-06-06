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

	# Invalidate a cache entry by handler name
	def invalidate(self, *, handlerName: str):
		# Scrub through the cache looking for a handler with a matching name in the cache
		for key in self.etagCache.keys():
			# If we've found one, then drop its entries to force a re-cache
			if key.__name__ == handlerName:
				del self.etagCache[key]
				del self.responseCache[key]
				# And stop so the iteration doesn't get grumpy at us
				break

# Defines the handling for an ETag cached request for JSON
class ETagJSONHandler:
	def __init__(self, cache: ETagCache, handler: JSONHandler):
		# Store the cache instance and handler we're wrapping
		self.cache = cache
		self.handler = handler

		# Copy a few properties from the handler function so Flask.route() works right
		self.__module__ = handler.__module__
		self.__name__ = handler.__name__
		self.__qualname__ = handler.__qualname__
		self.__doc__ = handler.__doc__
		self.__annotations__ = handler.__annotations__

	# Invoked when this handler is called on for a request
	def __call__(self):
		# Check to see if the request has an If-None-Match ETag header
		etag = request.headers.get('If-None-Match')
		# If the request does, look the handler up in the ETag cache and check if they match
		if etag is not None:
			# If the etag has been weakened (eg, because nginx did gzip compression), strip the weakening
			if etag.startswith('W/'):
				etag = etag[2:]
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
		# Mark it cached and enter it into the cache via computing its ETag
		response.headers['Cache-Control'] = 'max-age=604800, no-cache, public'
		self.cache.etag(self.handler, response)
		return response
