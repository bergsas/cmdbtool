# -*- coding: utf-8 -*-
import re
import codecs
import unicodedata
from libcmdb2.core import CMDBServer, resources
from libcmdb2.resources.common import Resource

class CMDB:
  class Client(object):
    class ResourceCache:
      def __init__(self, client, resource_name):
        self.client = client
        self.resource_name = resource_name
        self.resource_class = client.resources.get_class_for(resource_name)
        self.pk = self.resource_class.pk
        self.resource_schema = client.server.resource_schema(resource_name)
        self.display_name = self.resource_class.display_name_attrs
        self.required_attrs = self.resource_class.required_attrs
        self.optional_attrs = self.resource_class.optional_attrs

      def __repr__(self):
        return self.resource_name

    class Query:
      def __init__(self, client, resource):
        self.client = client
        self.resource = resource
        self.set_limit = None
        self.set_offset = None
        self.query = None
        self.uri = None

        self.json = None

        self.ready = False
      
      def make_ready(self, word):
        if word is None:
          self.uri = self.client.server._make_uri(self.resource)
        else:
          self.uri = self.client.server._make_uri(self.resource, **self.query)
        
        if not self.set_limit is None:
          if re.match('.*\?.*', self.uri):
            self.uri += "&limit=%d" %(self.set_limit)
          else:
            self.uri += "?limit=%d" %(self.set_limit)
 
        if not self.set_offset is None:
          if re.match('.*\?.*', self.uri):
            self.uri += "&offset=%d" %(self.set_offset)
          else:
            self.uri += "?offset=%d" %(self.set_offset)

      def object_query (self): 
        if self.uri is None:
          raise Exception("Not ready")

        if self.uri is False:
          return False

        self._dict = self.client.server._get_dict(self.uri)
        
        if 'next' in self._dict['meta'] and self._dict['meta']['next']:
          self.uri = self.client.server._server + self._dict['meta']['next']
        else:
          self.uri = False

        return self._dict['objects']
     
      def offset(self):
        return self._dict['meta']['offset']

      def limit(self):
        return self._dict['meta']['limit']

      def total_count(self):
        return self._dict['meta']['total_count']

    def new_query(self, resource, **kwargs):
      query = self.Query(self, resource)
      query.query = kwargs
      return query


    def __init__(self, server, api_path, user = None, api_key = None):
      # Initiate server object
      self.server = CMDBServer(server, api_path, user, api_key)
      self.resources = resources 
      self.resource_cache = {}
    
    def __repr__(self):
      return str(self.server._server)

    # Ugh
    def unicode_fallback(self, string):
      return unicodedata.normalize('NFKD', string).encode('ascii', 'ignore')

    # This is probably a very expensive way of doing it!
    def cache_resource(self, resource_name):
      # I hope I don't store that ''resource_name'' string too many times.
      if not resource_name in self.resource_cache:
        self.resource_cache[resource_name] = self.ResourceCache(self, resource_name) 
      return self.resource_cache[resource_name]
      
      # Currently there's no clean up of this cache. :)
      # Oh well. Python will collect my garbage.
 
    def dump_object(self,obj, ident=""): 

      # Get resource name for object
      name = obj.resource_name
  
      # If object resource isn't "cached", do so.
      cached = self.cache_resource(name)

      #print cached.resource_schema
      #for attr,item in cached.resource_schema.items():
      #  for key,subitem in item.items():
      #    try:
      #      print "%s.%s => %s"%(attr, key, subitem)
      #    except UnicodeEncodeError, e:
      #      print "%s.%s => %s" %(attr,key,self.unicode_fallback(subitem))
      #return

      # Max length of attribute name: For indentation
      maxlen = len(max(cached.required_attrs + cached.optional_attrs, key=len)) +1

      for n in cached.required_attrs + cached.optional_attrs:
        try:
          out = getattr(obj, n)
        except Exception, e:
          if n in obj._attrs._attrs:
            out = obj._attrs._attrs[n]
            print obj._cmdb_server._get_dict(obj._cmdb_server._server + out)
          else:
            out = e
        # Print attribute
        try:
          print "%s%-*s %s" %(ident, maxlen, str(n) + ":", out)
        except UnicodeEncodeError, e:
          print "%s%-*s %s" %(ident, maxlen, str(n) + ":",  self.unicode_fallback(out))
          print "%s%-*s ^^^ ERRORNEOUS OUTPUT: Mangled" %(ident, maxlen, "")

        # If attribute is a Resource object, dump that resource object as well
        if isinstance(out, Resource):
          self.dump_object(out, "  %s" %(ident))

    def resolve_object(self, obj, attr = None):
      if attr == None:
        print attr
    
    def compile_output(self, output, obj):
      compiled = []
      
      cached = self.cache_resource(obj.resource_name)
      for attr in output:
        if isinstance(attr, list):
          this_obj = obj
          for this_attr in attr:
            if this_attr in this_obj.required_attrs or this_attr in this_obj.optional_attrs:
              this_obj = getattr(this_obj, this_attr)
            else:
              print "Die die die! No such attr in %s: %s" %(this_obj.resource_name, this_attr)
              exit(1)
          compiled += ["obj." + ".".join(attr)]
        else:
          if not (attr in obj.required_attrs or attr in obj.optional_attrs):
            print "Die die die! No such attr in %s: %s" %(obj.resource_name, attr)
            exit(1)
          compiled += ["obj." + attr]
      # EVAL!!! EVIL AND DANGEROUS HACK. HACK HACK HACK.
      return compile(', '.join(compiled), '<string>', 'eval')
# vim: syntax=python
