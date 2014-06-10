# -*- coding: utf-8 -*-
import re
import codecs
import unicodedata
from libcmdb2.exceptions import *
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
      
      def make_ready(self):
        if self.query is None:
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
          self.make_ready()

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
      self.field_lookup_types = self.server.field_lookup_types
      self.dict_cache = {}

    #def __repr__(self):
    #  return str(self.server._server)

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
            #print obj._cmdb_server._get_dict(obj._cmdb_server._server + out)
          else:
            out = e
        # Print attribute
        try:
          if isinstance(out, Resource):
            print "%s%-*s" %(ident, maxlen, str(n) + ":")
            self.dump_object(out, "  %s" %(ident))
          else:
            print "%s%-*s %s" %(ident, maxlen, str(n) + ":", out)
        except UnicodeEncodeError, e:
          print "%s%-*s %s" %(ident, maxlen, str(n) + ":",  self.unicode_fallback(out))
          print "%s%-*s ^^^ ERRORNEOUS OUTPUT: Mangled" %(ident, maxlen, "")

        # If attribute is a Resource object, dump that resource object as well
    
    # Simply return a dict based on a uri.
    #   Cache the dicts. :)

    def get_dict(self, obj_uri, recurse = 0):
      if obj_uri in self.dict_cache:
        return self.dict_cache[obj_uri]
     
      self.dict_cache[obj_uri] = None # Placeholder to prevent recursion

      try:
        this = self.server._get_dict(self.server._server + obj_uri)
      except ServerError:
        return None

      if recurse > 0 or recurse < 0:
        recurse -= 1
        for key, item in this.items():
          if isinstance(item, basestring) and re.match("^/api/", item):
            val = self.get_dict(item, recurse)
            if val: 
              this[key] = val
      
      self.dict_cache[obj_uri] = this
      return this

    def default_output(self, obj):
      cr = self.cache_resource(obj.resource_name)
      output = cr.required_attrs[:]
      # http://stackoverflow.com/questions/2612802/how-to-clone-or-copy-a-list-in-python
      output.remove(cr.display_name)
      output = [cr.display_name] + output
      return output

    def sane_output(self, output, obj):
      sane = []
      cached = self.cache_resource(obj.resource_name)
      
#        if not isinstance(attr, list):
#          attr = [attr]
#        try:
#          for key in attr:
#            val = getattr(obj, key)
#          
#            if isinstance(val, Resource):
#              sane += [[key, '_display_name']]
#            else:
#              if isinstance(val, list):
#                if  cached.resource_schema[attr]['type'] == 'related':
#                  # may be implemented: namely: a recursion into these.
#                  continue
#        
#        except MissingImplementation:
#          continue
#          #print "blurp"

      for attr in output:
        val = obj
        
        
        if not isinstance(attr, list):
          keylist = [attr]
        else:
          keylist = attr[:]

        try:
          for key in keylist:
            val = getattr(val, key)

        except MissingImplementation:
          dummy = True  #  :)
        
        #libcmdb2.resources.common.RequiredAttributeMissingError: 'durationnormal' missing!
        except resources.common.RequiredAttributeMissingError:
          dummy = True # :)

        except AttributeError, e:
          continue

        if isinstance(val, Resource):
          keylist += ['_display_name']


        sane += [keylist]


      return sane


    def generate_output_format(self, output):
      return '\t'.join(['%s'] * len(output))

    def compile_output(self, output, obj):
      compiled = []
     
      cached = self.cache_resource(obj.resource_name)
      for attr in output:
        if not isinstance(attr, list):
          attr = [attr]

        build = []
        this_obj = obj
        try:
          for this_attr in attr:
            if this_attr in this_obj.required_attrs or this_attr in this_obj.optional_attrs or this_attr == '_display_name':
              this_obj = getattr(this_obj, this_attr)
              build += [this_attr]
            else:
              print "Die die die! No such attr in %s: %s" %(this_obj.resource_name, this_attr)
              exit(1)
        # Hacky ways are, well, my way.
        except MissingImplementation, e:
          if this_attr in this_obj._attrs.__dict__["_attrs"]:
            build += ['_attrs','__dict__["_attrs"]["%s"]' %(this_attr)]

        except resources.common.RequiredAttributeMissingError:
          if this_attr in this_obj._attrs.__dict__["_attrs"]:
            build += ['_attrs','__dict__["_attrs"]["%s"]' %(this_attr)]

        compiled += ["obj." + ".".join(build)]
      # EVAL!!! EVIL AND DANGEROUS HACK. HACK HACK HACK.
     
      if compiled:
        return compile(', '.join(compiled), '<string>', 'eval')
      
      return None

    # operator: [case sensitive, case insensitive]

    search_operators = {
      '==':  ['contains','icontains'],
      '===': ['exact','iexact'],
      '>':   ['gt','gt'],
      '>=':  ['gte','gte'],
      '~':   ['regex','iregex'],
      '<':   ['lt','lt'],
      '<=':  ['lte','lte']
    }

   #(
   #  'contains',          ==
   #  'day',         ***
   #  'endswith',    ***
   #  'exact',             ===
   #  'gt',                >
   #  'gte',               >=
   #  'icontains',         ==
   #  'iendswith',   ***
   #  'iexact',            ===
   #  'in',          ***
   #  'iregex',            ~
   #  'isnull',      ***
   #  'istartswith', *** 
   #  'lt',                <
   #  'lte',               <=
   #  'month',       ***
   #  'range',       ***
   #  'regex',             ~
   #  'search',      ***
   #  'startswith',  ***
   #  'week_day',    ***
   #  'year'         ***
   #)

    def init_basic_search(self, resource, query, **options):
      cr = self.cache_resource(resource)
      #print cr.resource_schema
      #print cr.required_attrs
      #print cr.optional_attrs
      #print  cr

      case_insensitive = 1

      if 'case-sensitive' in options:
        case_insensitive = 0

      if len(query) == 0:
        return {}

      pattern = re.compile(r"(^(([^=~<>!:]*)([=~<>!:]+))?(.*$))")

      
      dic = {}
      for item in query:
        split = pattern.match(item)
        var, operator, data = split.group(3), split.group(4), split.group(5)
        
        if var == None or len(var) == 0:
          var = cr.display_name
        
        if operator == None:
          operator = self.search_operators.keys()[0]
        
        if not operator in self.search_operators:
          # Lazy me. Lazy me!
          print "Unknown operator: %s in %s" %(operator, "init_basic_search")
          exit(1)  # This is not good. I should use raise, really.

        dic['__'.join(var.split('.') + [self.search_operators[operator][case_insensitive]])] = data

      return dic
        
# vim: syntax=python
