DEFAULT RESOURCE: host
----------------------

By default cmdbtool queries the ''host'' resource. This can be changed with
the -r switch. 

  $ cmdbtool pc4442
  pc4442  [u'/api/v2/function/26/']       <Item - pk: 2854, XXXX>   <OS - pk: 9, Linux Ubuntu 12.04 Precise Pangolin amd64> /api/v2/prodlevel/4/    /api/v2/ratype/6/

  $ cmdbtool -r item serial==XXXX
  XXXX      <Manufacturer - pk: 27, HP>     <ItemModel - pk: 506, Compaq elite 8300SFF>     /api/v2/itemsupport/28/ <Location - pk: 1, Hovedbygget Oslo><Vendor - pk: 2, Dell>   <StatusCode - pk: 3, AKTIV>

USING 

  $ cmdbtool item.serial==XXXX
  pc4442  [u'/api/v2/function/26/']       <Item - pk: 2854, XXXX>   <OS - pk: 9, Linux Ubuntu 12.04 Precise Pangolin amd64> /api/v2/prodlevel/4/    /api/v2/ratype/6/


QUERY-LIMIT
-----------

By default cmdb only returns 20 hits per query. You may therefore want to set
your query limit to something higher if you expect more than 20 hits. Or
indeed to 0 to return everything:

  $ cmdbtool --query-limit=0 ~pc | wc -l
  801

  $ cmdbtool ~pc | wc -l
  20

Here we see that we've got 801 host items that match pc, while cmdbtool
will only return 20 if you don't disable the query-limit.



