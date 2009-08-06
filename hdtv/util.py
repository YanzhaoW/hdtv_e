# -*- coding: utf-8 -*-

# HDTV - A ROOT-based spectrum analysis software
#  Copyright (C) 2006-2009  The HDTV development team (see file AUTHORS)
#
# This file is part of HDTV.
#
# HDTV is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# HDTV is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with HDTV; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import math
import re
import os
import glob

def GetCompleteOptions(begin, options):
    l = len(begin)
    return [o + " " for o in options if o[0:l] == begin]

def Median(values):
    """
    Calculate Median of list
    """
    values.sort()
    n = len(values)
    if not n:
        return None
    
    if n % 2 == 0: 
        return (values[(n-1)/2] + values[n/2]) * 0.5
    else:
        return values[n/2]

class ErrValue:
    """
    A value with an error
    
    values may be given as floats or strings containing value and error in
    the form "12.3456(78)" if no error is given.
     
    Beware: Error propagation is only working for statistically independant 
    values for now!
    """
    def __init__(self, value, error=0):
                
        if isinstance(value, str):
            tmp = self._fromString(value)
            self.value = tmp[0]
            self.error = tmp[1]
        else:
            try:
                self.error = abs(error) # Errors are always positive
            except TypeError:
                self.error = error
            self.value = value    
        try:
            self.rel_error = self.error / self.value * 100.0 # Error in percent
        except (ZeroDivisionError, TypeError):
            self.rel_error = None
    
    
    def __repr__(self):
        return "ErrValue(" + repr(self.value) + ", " + repr(self.error) + ")"
    
    def __str__(self):
        return self.fmt()

    def __eq__(self, other):
        """
        Test for equality; taking errors into account
        """
        # Check given objects
        val1 = self._sanitize(self)
        val2 = self._sanitize(other)
        
        # Do the comparison
        if (abs(val1.value - val2.value) <= (val1.error + val2.error)):
            return True
        else:
            return False
        
    def __cmp__(self, other):
        """
        compare by value
        """
        # Check given objects
        
        otherval = self._sanitize(other)
        
        return cmp(self.value, otherval.value)
    
    def __add__(self, other):
        """Add two values with error propagation"""
        val1 = self._sanitize(self)
        val2 = self._sanitize(other)
        ret  = ErrValue(0, 0)
        
        ret.value = val1.value + val2.value
        ret.error = math.sqrt(math.pow(val1.error, 2) + math.pow(val2.error, 2))
        return ret

    def __radd__(self, other):
        return self.__add__(other)
    
    
    def __difference(self, minuend, subtrahend):
        """Subtract two values with error propagation"""
        val1 = self._sanitize(minuend)
        val2 = self._sanitize(subtrahend)
        ret  = ErrValue(0,0)
        
        ret.value = val1.value - val2.value
        ret.error = math.sqrt(math.pow(val1.error, 2) + math.pow(val2.error, 2))

        return ret

    def __sub__(self, other):
        return self.__difference(self, other)
    
    def __rsub__(self, other):
        return self.__difference(other, self)

    def __mul__(self, other):
        """Multiply two values with error propagation"""
        val1 = self._sanitize(self)
        val2 = self._sanitize(other)
        ret  = ErrValue(0,0)
        
        ret.value = val1.value * val2.value
        ret.error = math.sqrt(math.pow((val1.value * val2.error), 2) \
                              + math.pow((val2.value * val1.error), 2))
        return ret

    def __rmul__(self, other):
        return self.__mul__(other)
    
    
    def __quotient(self, dividend, divisor):
        """Divide two values with error propagation"""
        val1 = self._sanitize(dividend)
        val2 = self._sanitize(divisor)
        ret  = ErrValue(0,0)
        
        ret.value = val1.value / val2.value
        ret.error = math.sqrt(math.pow((val1.error / val2.value), 2) \
                              + math.pow((val1.value * val2.error / math.pow(val2.value,2)), 2))
        return ret
        
    def __div__(self, other):
        return self.__quotient(self, other)
    
    def __rdiv__(self, other):
        return self.__quotient(other, self)
    
    def __float__(self):
        return float(self.value)
    
    def _sanitize(self, val):
        """
        * Convert floats or strings to ErrValue
        * Return .error=0 for .error==None values to be able to do calculations
        """
        ret = ErrValue(0, 0)
               
        try:
            ret.value = val.value
            ret.error = abs(val.error)
        except TypeError:
            ret.value = val.value
            ret.error = 0
        except AttributeError:
            ret.value = val
            ret.error = 0
            
        return ret
        
        
    def __abs__(self):
        return ErrValue(abs(self.value), self.error)
    
    def _fromString(self, strvalue):
        """
        Convert values with error given as strings (e.g. "0.1234(56)") to
        ErrValues
        """
        
        try: # Try to convert string values like "0.1234(56)" into numbers
            # TODO: Handle decimal seperator properly, depending on locale
            val_string = re.match(r"([0-9\.]+)\(([0-9]+)\)", strvalue)
            value = float(val_string.group(1))
            error = float(val_string.group(2))
            tmp = value
            while tmp % 1 != 0: # Determine magnitude of error
                tmp *= 10
                error /=10
        except TypeError: # No string given
            return (strvalue, None)
        except AttributeError: # String does not contain error
            value = float(strvalue)
            error = 0
        
        return (value, error)
        
    
    def fmt(self):
    
        try:
            # Call fmt_no_error() for values without error
            if self.error == 0:
                return self.fmt_no_error()

            # Check and store sign
            if self.value < 0:
                sgn = "-"
                value = -self.value
            else:
                sgn = ""
                value = self.value
                
            error = self.error
        
            # Check whether to switch to scientific notation
            # Catch the case where value is zero
            try:
                log10_val = math.floor(math.log(value) / math.log(10.))
            except (ValueError, OverflowError):
                log10_val = 0.

            if log10_val >= 6 or log10_val <= -2:
                # Use scientific notation
                suffix = "e%d" % int(log10_val)
                exp = 10 ** log10_val
                value /= exp
                error /= exp
            else:
                # Use normal notation
                suffix = ""
                
            # Find precision (number of digits after decimal point) needed such that the
            # error is given to at least two decimal places
            if error >= 10.:
                prec = 0
            else:
                # Catch the case where error is zero
                try:
                    prec = -math.floor(math.log(error) / math.log(10.)) + 1
                except (ValueError, OverflowError):
                    prec = 6
                    
            # Limit precision to sensible values, and capture NaN
            #  (Note that NaN is by definition unequal to itself)
            if prec > 20:
                prec = 20
            elif prec != prec:
                prec = 3
                
            return "%s%.*f(%.0f)%s" % (sgn, int(prec), value, error * 10 ** prec, suffix)
        
        except (ValueError, TypeError):
            return ""
    
    def fmt_full(self):
        """
        Print ErrValue with absolute and relative error
        """
        string = str(self.fmt()) + " [" + "%.*f" % (2, self.rel_error) + "%]"
        return string 
        
    def fmt_no_error(self, prec=6):
        try:
            # Check and store sign
            if self.value < 0:
                sgn = "-"
                value = -self.value
            else:
                sgn = ""
                value = self.value
                
            # Check whether to switch to scientific notation
            # Catch the case where value is zero
            try:
                log10_val = math.floor(math.log(value) / math.log(10.))
            except (ValueError, OverflowError):
                log10_val = 0.
            
            if log10_val >= 6 or log10_val <= -2:
                # Use scientific notation
                suffix = "e%d" % int(log10_val)
                value /= 10 ** log10_val
            else:
                # Use normal notation
                suffix = ""
                
            return "%s%.*f%s" % (sgn, prec, value, suffix)
        except (ValueError, TypeError):
            return ""

class Linear:
    """
    A linear relationship, i.e. y = p1 * x + p0
    """
    def __init__(self, p0=0., p1=0.):
        self.p0 = p0
        self.p1 = p1
        
    def Y(self, x):
        """
        Get y corresponding to a certain x
        """
        return self.p1 * x + self.p0
        
    def X(self, y):
        """
        Get x corresponding to a certain y
        May raise a ZeroDivisionError
        """
        return (y - self.p0) / self.p1
        
    @classmethod
    def FromXYPairs(cls, a, b):
        """
        Construct a linear relationship from two (x,y) pairs
        """
        l = cls()
        l.p1 = (b[1] - a[1]) / (b[0] - a[0])
        l.p0 = a[1] - l.p1 * a[0]
        return l
        
    @classmethod
    def FromPointAndSlope(cls, point, p1):
        """
        Construct a linear relationship from a slope and a point ( (x,y) pair )
        """
        l = cls()
        l.p1 = p1
        l.p0 = point[1] - l.p1 * point[0]
        return l


class TxtFile(object):
    """
    Handle txt files, ignoring commented lines
    """
    def __init__(self, filename, mode="r"):
                
        self.lines = list()  
        self.mode = mode
        filename = filename.rstrip() # TODO: this has to be handled properly (escaped whitespaces, etc...)
        self.filename = os.path.expanduser(filename) 
        self.fd = None
        
    def read(self, verbose=False):
        try:
            self.fd = open(self.filename, self.mode)
            prev_line = ""
            for line in self.fd:
                line = line.rstrip('\r\n ')
                if len(line) > 0 and line[-1] == '\\': # line is continued on next line
                    prev_line += line.rstrip('\\') 
                    continue
                else:
                    if prev_line != "":
                        line = prev_line + " " + line
                    prev_line = ""
                if verbose:
                    print "file>", line
                
                # Strip comments 
                line = line.split("#")[0] 
                if line == "":
                    continue
                self.lines.append(line)
                
        except IOError, msg:
            print "Error opening file:", msg
        except: # Let MainLoop handle other exceptions
            raise
        finally:
            if not self.fd is None:
                self.fd.close()
                
    def write(self, line):
        """
        TODO
        """
        pass
    
class Pairs(list):
    """
    List of pair values
    """
    def __init__(self, conv_func=lambda x: x): # default conversion is "identity" -> No conversion
        
        super(Pairs, self).__init__()
        self.conv_func = conv_func # Conversion function, e.g. float
        
    def add(self, x, y):
        """
        Add a pair
        """
        self.append([self.conv_func(x), self.conv_func(y)])
        
    def remove(self, pair):
        """
        TODO
        """
        pass
        
    def fromFile(self, fname):
        """
        Read pairs from file
        """    
        file = TxtFile(fname)
        file.read()
        for line in file.lines:
            pair = line.split()
            try:
                self.add(pair[0], pair[1])
            except ValueError:
                print "Invalid Line in", fname, ":", line
        
        

