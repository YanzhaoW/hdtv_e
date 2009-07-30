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

#-------------------------------------------------------------------------------
# For each model implemented on the C++ side, we have a corresponding Python
# class to handle fitter setup and data transfer to the Python side
#-------------------------------------------------------------------------------
import ROOT
import hdtv.util

hdtv.dlmgr.LoadLibrary("display")



class FitValue(hdtv.util.ErrValue):
    """
    Error Value combined with status of parameter
    """
    def __init__(self, value, error, free):
        hdtv.util.ErrValue.__init__(self, value, error)
        self.free = free
        
    def fmt(self):
        if self.free:
            return hdtv.util.ErrValue.fmt(self)
        else:
            return hdtv.util.ErrValue.fmt_no_error(self) + " (HOLD)"


# Base class for all peak models
class PeakModel:
    """
    A peak model is a function used to fit peaks. The user can choose how to fit
    its parameters (and whether to include them at all, i.e. for tails). After
    everything has been configured, the peak model produces a C++ fitter object.
    """
    def __init__(self):
        self.fGlobalParams = dict()

    def ResetGlobalParams(self):
        self.fGlobalParams.clear()
        
    def OrderedParamKeys(self):
        """
        Return the names of all peak parameters in the preferred ordering
        """
        return self.fOrderedParamKeys
        
    def OptionsStr(self):
        """
        Returns a string describing the currently set parameters of the model
        """
        statstr = ""
        
        for name in self.OrderedParamKeys():
            status = self.fParStatus[name]

            # Short format for multiple values...
            if type(status) == list:
                statstr += "%s: " % name
                sep = ""
                for stat in status:
                    statstr += sep
                    if stat in ("free", "equal", "hold", "none", "calculated"):
                        statstr += stat
                    else:
                        statstr += "%.3f" % stat
                    sep = ", "
                statstr += "\n"

            # ... long format for a single value
            else:
                if status == "free":
                    statstr += "%s: (individually) free\n" % name
                elif status == "equal":
                    statstr += "%s: free and equal\n" % name
                elif status == "hold":
                    statstr += "%s: held at default value\n" % name
                elif status == "none":
                    statstr += "%s: none (disabled)\n" % name
                elif status == "calculated":
                    statstr += "%s: calculated\n" %name
                else:
                    statstr += "%s: fixed at %.3f\n" % (name, status)
                    
        return statstr
        
    def CheckParStatusLen(self, minlen):
        """
        Checks if each parameter status provided on a peak-by-peak basis
        has at least minlen entires. Raises a RuntimeError with an appropriate
        error message if the check fails.
        """
        for (parname, status) in self.fParStatus.iteritems():
            if type(status) == list and len(status) < minlen:
                raise RuntimeError, "Not enough values for status of %s" % parname
        
    def ParseParamStatus(self, parname, status):
        """
        Parse a parameter status specification string
        """
        # Case-insensitive matching
        status = status.strip().lower()
    
        # Check to see if status corresponds, possibly abbreviated,
        #  to a number of special keywords
        stat = None
        if len(status) < 1:
            raise ValueError
        elif "free"[0:len(status)] == status:
            stat = "free"
        elif "equal"[0:len(status)] == status:
            stat = "equal"
        elif "none"[0:len(status)] == status:
            stat = "none"
        elif "hold"[0:len(status)] == status:
            stat = "hold"
        elif "calculated"[0:len(status)]==status:
            stat = "calculated"
    
        # If status was a keyword, see if this setting is legal for the
        #  parameter in question
        if not stat is None and stat in self.fValidParStatus[parname]:
            return stat
        # If status was not a keyword, try to parse it as a float
        if float in self.fValidParStatus[parname]:
            return float(status)
        # if it is nothing of the above
        raise RuntimeError, "Invalid status %s for parameter %s" % (status, parname)

        
    def SetParameter(self, parname, status):
        """
        Set status for a certain parameter
        """
        parname = parname.strip().lower()
        
        if not parname in self.fValidParStatus.keys():
            raise RuntimeError, "Invalid parameter name"
            
        if "," in status:
            self.fParStatus[parname] = map(lambda s: self.ParseParamStatus(parname, s),
                                           status.split(","))
        else:
            self.fParStatus[parname] = self.ParseParamStatus(parname, status)
        

    def GetParam(self, name, peak_id, pos_uncal, cal, ival=None):
        """
        Return an appropriate HDTV.Fit.Param object for the specified parameter
        """
        # See if the parameter status has been specified for each peak
        # individually, or for all peaks at once
        if type(self.fParStatus[name]) == list:
            parStatus = self.fParStatus[name][peak_id]
        else:
            parStatus = self.fParStatus[name]
        # Switch according to parameter status
        if parStatus == "equal":
            if not name in self.fGlobalParams:
                if ival == None:
                    self.fGlobalParams[name] = self.fFitter.AllocParam()
                else:
                    self.fGlobalParams[name] = self.fFitter.AllocParam(ival)
            return self.fGlobalParams[name]
        elif parStatus == "free":
            if ival == None:
                return self.fFitter.AllocParam()
            else:
                return self.fFitter.AllocParam(ival)
        elif parStatus == "hold":
            if ival == None:
                return ROOT.HDTV.Fit.Param.Fixed()
            else:
                return ROOT.HDTV.Fit.Param.Fixed(ival)
        elif parStatus == "none":
            return ROOT.HDTV.Fit.Param.None()
        elif type(parStatus) == float:
            return ROOT.HDTV.Fit.Param.Fixed(self.Uncal(name, parStatus, pos_uncal, cal))
        else:
            raise RuntimeError, "Invalid parameter status"


