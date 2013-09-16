##############################################################################
# Copyright 2009, Gerhard Weis
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#  * Neither the name of the authors nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT
##############################################################################
'''
This module provides an ISO 8601:2004 time zone info parser.

It offers a function to parse the time zone offset as specified by ISO 8601.
'''
import re

from isodate.isoerror import ISO8601Error
from isodate.tzinfo import UTC, FixedOffset, ZERO

TZ_REGEX = r"(?P<tzname>(Z|(?P<tzsign>[+-])"\
           r"(?P<tzhour>[0-9]{2})(:(?P<tzmin>[0-9]{2}))?)?)"

TZ_RE = re.compile(TZ_REGEX)

def build_tzinfo(tzname, tzsign='+', tzhour=0, tzmin=0):
    '''
    create a tzinfo instance according to given parameters.

    tzname:
      'Z'       ... return UTC
      '' | None ... return None
      other     ... return FixedOffset
    '''
    if tzname is None or tzname == '':
        return None
    if tzname == 'Z':
        return UTC
    tzsign = ((tzsign == '-') and -1) or 1
    return FixedOffset(tzsign * tzhour, tzsign * tzmin, tzname)

def parse_tzinfo(tzstring):
    '''
    Parses ISO 8601 time zone designators to tzinfo objecs.

    A time zone designator can be in the following format:
              no designator indicates local time zone
      Z       UTC
      +-hhmm  basic hours and minutes
      +-hh:mm extended hours and minutes
      +-hh    hours
    '''
    match = TZ_RE.match(tzstring)
    if match:
        groups = match.groupdict()
        return build_tzinfo(groups['tzname'], groups['tzsign'],
                            int(groups['tzhour'] or 0),
                            int(groups['tzmin'] or 0))
    raise ISO8601Error('%s not a valid time zone info' % tzstring)

def tz_isoformat(dt, format='%Z'):
    '''
    return time zone offset ISO 8601 formatted.
    The various ISO formats can be chosen with the format parameter.

    if tzinfo is None returns ''
    if tzinfo is UTC returns 'Z'
    else the offset is rendered to the given format.
    format:
        %h ... +-HH
        %z ... +-HHMM
        %Z ... +-HH:MM
    '''
    tzinfo = dt.tzinfo
    if (tzinfo is None) or (tzinfo.utcoffset(dt) is None):
        return ''
    if tzinfo.utcoffset(dt) == ZERO and tzinfo.dst(dt) == ZERO:
        return 'Z'
    tdelta = tzinfo.utcoffset(dt)
    seconds = tdelta.days * 24 * 60 * 60 + tdelta.seconds
    sign = ((seconds < 0) and '-') or '+'
    seconds = abs(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 99:
        raise OverflowError('can not handle differences > 99 hours')
    if format == '%Z':
        return '%s%02d:%02d' % (sign, hours, minutes)
    elif format == '%z':
        return '%s%02d%02d' % (sign, hours, minutes)
    elif format == '%h':
        return '%s%02d' % (sign, hours)
    raise AttributeError('unknown format string "%s"' % format)
