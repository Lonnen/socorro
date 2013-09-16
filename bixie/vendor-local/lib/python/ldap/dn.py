"""
dn.py - misc stuff for handling distinguished names (see RFC 4514)

See http://www.python-ldap.org/ for details.

\$Id: dn.py,v 1.11 2010/06/03 12:26:39 stroeder Exp $

Compability:
- Tested with Python 2.0+
"""

from ldap import __version__


import _ldap

import ldap.functions


def escape_dn_chars(s):
  """
  Escape all DN special characters found in s
  with a back-slash (see RFC 4514, section 2.4)
  """
  if s:
    s = s.replace('\\','\\\\')
    s = s.replace(',' ,'\\,')
    s = s.replace('+' ,'\\+')
    s = s.replace('"' ,'\\"')
    s = s.replace('<' ,'\\<')
    s = s.replace('>' ,'\\>')
    s = s.replace(';' ,'\\;')
    s = s.replace('=' ,'\\=')
    s = s.replace('\000' ,'\\\000')
    if s[0]=='#' or s[0]==' ':
      s = ''.join(('\\',s))
    if s[-1]==' ':
      s = ''.join((s[:-1],'\\ '))
  return s


def str2dn(dn,flags=0):
  """
  This function takes a DN as string as parameter and returns
  a decomposed DN. It's the inverse to dn2str().

  flags describes the format of the dn

  See also the OpenLDAP man-page ldap_str2dn(3)
  """
  if not dn:
    return []
  return ldap.functions._ldap_function_call(None,_ldap.str2dn,dn,flags)


def dn2str(dn):
  """
  This function takes a decomposed DN as parameter and returns
  a single string. It's the inverse to str2dn() but will always
  return a DN in LDAPv3 format compliant to RFC 4514.
  """
  return ','.join([
    '+'.join([
      '='.join((atype,escape_dn_chars(avalue or '')))
      for atype,avalue,dummy in rdn])
    for rdn in dn
  ])

def explode_dn(dn,notypes=0,flags=0):
  """
  explode_dn(dn [, notypes=0]) -> list

  This function takes a DN and breaks it up into its component parts.
  The notypes parameter is used to specify that only the component's
  attribute values be returned and not the attribute types.
  """
  if not dn:
    return []
  dn_decomp = str2dn(dn,flags)
  rdn_list = []
  for rdn in dn_decomp:
    if notypes:
      rdn_list.append('+'.join([
        escape_dn_chars(avalue or '')
        for atype,avalue,dummy in rdn
      ]))
    else:
      rdn_list.append('+'.join([
        '='.join((atype,escape_dn_chars(avalue or '')))
        for atype,avalue,dummy in rdn
      ]))
  return rdn_list


def explode_rdn(rdn,notypes=0,flags=0):
  """
  explode_rdn(rdn [, notypes=0]) -> list

  This function takes a RDN and breaks it up into its component parts
  if it is a multi-valued RDN.
  The notypes parameter is used to specify that only the component's
  attribute values be returned and not the attribute types.
  """
  if not rdn:
    return []
  rdn_decomp = str2dn(rdn,flags)[0]
  if notypes:
    return [avalue or '' for atype,avalue,dummy in rdn_decomp]
  else:
    return ['='.join((atype,escape_dn_chars(avalue or ''))) for atype,avalue,dummy in rdn_decomp]
