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
import ROOT
import hdtv.cmdline
import hdtv.cmdhelper
import hdtv.options
import hdtv.util
import hdtv.ui

import copy
import sys

class FitInterface:
    """
    User interface for fitting 1-d spectra
    """
    def __init__(self, spectra):
        hdtv.ui.msg("Loaded user interface for fitting of 1-d spectra")

        self.spectra = spectra
        self.window = self.spectra.window

        # tv commands
        self.tv = TvFitInterface(self)

        # Register configuration variables for fit interface
        # default region width for quickfit
        opt = hdtv.options.Option(default = 20.0)
        hdtv.options.RegisterOption("fit.quickfit.region", opt) 

        
        # Register hotkeys
        self.window.AddHotkey(ROOT.kKey_b, 
                                lambda: self.spectra.SetMarker("bg"))
        self.window.AddHotkey([ROOT.kKey_Minus, ROOT.kKey_b],
                                lambda: self.spectra.RemoveMarker("bg"))
        self.window.AddHotkey(ROOT.kKey_r, 
                                lambda: self.spectra.SetMarker("region"))
        self.window.AddHotkey([ROOT.kKey_Minus, ROOT.kKey_r],
                                lambda: self.spectra.RemoveMarker("region"))
        self.window.AddHotkey(ROOT.kKey_p, 
                                lambda: self.spectra.SetMarker("peak"))
        self.window.AddHotkey([ROOT.kKey_Minus, ROOT.kKey_p],
                                lambda: self.spectra.RemoveMarker("peak"))
        self.window.AddHotkey(ROOT.kKey_B, 
                                lambda: self.spectra.ExecuteFit(peaks = False))
        self.window.AddHotkey(ROOT.kKey_F, 
                                lambda: self.spectra.ExecuteFit(peaks = True))
        self.window.AddHotkey([ROOT.kKey_Minus, ROOT.kKey_B], 
                                lambda: self.spectra.ClearFit(bg_only=True))
        self.window.AddHotkey([ROOT.kKey_Minus, ROOT.kKey_F], 
                                lambda: self.spectra.ClearFit(bg_only=False))
        self.window.AddHotkey(ROOT.kKey_Q, self.QuickFit)
        self.window.AddHotkey([ROOT.kKey_Plus, ROOT.kKey_F], self.spectra.StoreFit)
        self.window.AddHotkey([ROOT.kKey_Minus, ROOT.kKey_F], self.spectra.ClearFit)
        self.window.AddHotkey(ROOT.kKey_D, lambda: self.workFit.SetDecomp(True))
        self.window.AddHotkey([ROOT.kKey_Minus, ROOT.kKey_D], lambda: self.workFit.SetDecomp(False))

        self.window.AddHotkey([ROOT.kKey_f, ROOT.kKey_s],
                        lambda: self.window.EnterEditMode(prompt = "Show Fit: ",
                        handler = self._HotkeyShow))
        self.window.AddHotkey([ROOT.kKey_f, ROOT.kKey_a],
                        lambda: self.window.EnterEditMode(prompt = "Activate Fit: ",
                        handler = self._HotkeyActivate))
        self.window.AddHotkey([ROOT.kKey_f, ROOT.kKey_p], lambda: self._HotkeyShow("PREV"))
        self.window.AddHotkey([ROOT.kKey_f, ROOT.kKey_n], lambda: self._HotkeyShow("NEXT"))
    
    
    def _HotkeyShow(self, args):
        """
        Show wrapper for use with a Hotkey (internal use)
        """
        spec = self.spectra.GetActiveObject()
        if spec is None:
            self.window.viewport.SetStatusText("No active spectrum")
            return
        try:
            ids = hdtv.cmdhelper.ParseIds(args, spec)
        except ValueError:
            self.window.viewport.SetStatusText("Invalid fit identifier: %s" % args)
            return
        spec.ShowObjects(ids)
  

    def _HotkeyActivate(self, args):
        """
        ActivateObject wrapper for use with a Hotkey (internal use)
        """
        spec = self.spectra.GetActiveObject()
        if spec is None:
            self.window.viewport.SetStatusText("No active spectrum")
            return
        try:
            ids = hdtv.cmdhelper.ParseIds(args, spec)
        except ValueError:
            self.window.viewport.SetStatusText("Invalid fit identifier: %s" % args)
            return
        if len(ids) == 1:
            self.window.viewport.SetStatusText("Activating fit %s" %ids[0])
            self.spectra.ActivateFit(ids[0])
        elif len(ids) == 0:
            self.window.viewport.SetStatusText("Deactivating fit")
            self.spectra.ActivateFit(None)
        else:
            self.window.viewport.SetStatusText("Can only activate one fit")
       
       
    def ExecuteRefit(self, specID, fitID, peaks=True):
        """
        Re-Execute Fit on store fits
        """
        try:
            spec = self.spectra.dict[specID]
        except KeyError:
            raise KeyError, "invalid spectrum ID"
        try:
            fit = spec.dict[fitID]
        except KeyError:
            raise KeyError, "invalid fit ID"
        if peaks:
            fit.FitPeakFunc(spec, silent=False)
        else:
            fit.FitBgFunc(spec)
        fit.Draw(self.window.viewport)
            

    def QuickFit(self, pos=None):
        """
        Set region and peak markers automatically and do a quick fit as position "pos".
        
        If pos is not given, use cursor position
        """
        if pos is None:
            pos = self.window.viewport.GetCursorX()
        self.spectra.ClearFit()
        region_width = hdtv.options.Get("fit.quickfit.region")
        self.spectra.SetMarker("region", pos - region_width / 2.)
        self.spectra.SetMarker("region", pos + region_width / 2.)
        self.spectra.SetMarker("peak", pos)
        self.spectra.ExecuteFit()
        
    def ListFits(self, sid=None, ids=None, sortBy=None, reverseSort=False):
        """
        List results of stored fits as nice table
        """
        if sid is None:
            sid = self.spectra.activeID
        spec = self.spectra.dict[sid]
        # if there are not fits for this spectrum, there is not much to do
        if len(spec.ids) == 0:
            hdtv.ui.newline()
            hdtv.ui.msg("Spectrum " + str(sid) + " (" + spec.name + "): No fits")                
            hdtv.ui.newline()
            return
        # create result header
        result_header = "Fits in Spectrum " + str(sid) + " (" + spec.name + ")" + "\n"
        if ids is None:
            ids = spec.ids
        fits = [spec.dict[ID] for ID in ids]
        count_fits = len(fits)
        (objects, params) = self.ExtractFits(fits)

        # create result footer
        result_footer = "\n" + str(len(objects)) + " peaks in " + str(count_fits) + " fits."
        # create the table
        try:
            table = hdtv.util.Table(objects, params, sortBy=sortBy, reverseSort=reverseSort,
                                    extra_header = result_header, extra_footer = result_footer)
            hdtv.ui.msg(str(table))
        except KeyError:
            hdtv.ui.error("Spectrum " + str(sid) + ": No such attribute: " + str(sortBy))
            hdtv.ui.error("Spectrum " + str(sid) + ": Valid attributes are: " + str(params))
            
    def PrintWorkFit(self):
        """
        Print results of workFit as nice table
        """
        fit = self.spectra.workFit
        if fit.spec is not None:
            (objects, params) = self.ExtractFits([fit])
            header = "WorkFit on spectrum: " + str(fit.spec.ID) + " (" + fit.spec.name + ")"
            footer = "\n" + str(len(objects)) + " peaks in WorkFit"
            table = hdtv.util.Table(objects, list(params), sortBy="id",
                                    extra_header = header, extra_footer = footer)
            hdtv.ui.msg(str(table))
    
    def ExtractFits(self, fits):
        """
        Helper function for use with ListFits and PrintWorkFit functions.
        
        Return values:
            fitlist    : a list of dicts for each peak in the fits
            params     : a ordered list of valid parameter names
        """
        fitlist = list()
        params = list()
        # loop through fits
        for fit in fits:
            # Get peaks
            (peaklist, fitparams) = self.ExtractPeaklist(fit)
            if len(peaklist)==0:
                continue
            # update list of valid params
            for p in fitparams:
                # do not use set operations here to keep order of params
                if not p in params:
                    params.append(p)
            # add peaks to the list
            fitlist.extend(peaklist)
        return (fitlist, params)
               
    def ExtractPeaklist(self, fit):
        """
        Helper function for use with ListFits and PrintWorkFit functions.
        
        Return values:
            peaklist: a list of dicts for each peak in the fit
            params  : a ordered list of valid parameter names 
        """
        peaklist = list()
        params = ["id", "stat"]
        # Get peaks
        for peak in fit.peaks:
            thispeak = dict()
            if fit.ID is None:
                thispeak["id"] = "." + str(fit.peaks.index(peak))
            else:
                thispeak["id"] = str(fit.ID)+"." + str(fit.peaks.index(peak))
            thispeak["stat"] = str()
            if fit.active:
                thispeak["stat"] += "A"
            if fit.ID in fit.spec.visible or fit.ID is None:   # ID of workFit is None
                thispeak["stat"] += "V"
            # get parameter of this fit
            for p in fit.fitter.peakModel.fOrderedParamKeys:
                if p == "pos": 
                    # Store channel additionally to position
                    thispeak["channel"] = getattr(peak, "pos")
                    if "channel" not in params:
                        params.append("channel")
                # Use calibrated values of params if available 
                p_cal = p + "_cal"   
                if hasattr(peak, p_cal):
                    thispeak[p] = getattr(peak, p_cal)
                if p not in params:
                    params.append(p)
            # Calculate normalized volume if efficiency calibration is present
            # FIXME: does this belong here?
            if fit.spec.effCal is not None:
                volume = thispeak["vol"]
                par_index = params.index("vol") + 1
                energy = thispeak["pos"]
                norm_volume = volume / spec.effCal(energy)
                thispeak["vol/eff"] = norm_volume
            peaklist.append(thispeak)
        return (peaklist, params)
        
    def ShowFitterStatus(self, ids=None, default = False):
        """
        Show status of the fit parameters of the work Fit.
        
        If default is true, the status of the default Fitter is shown in addition.
        If a list of ids is given, the status of the fitters belonging to that 
        fits is also shown. Note, that the latter will silently fail for invalid 
        IDs.
        """
        if ids is None:
            ids = list()
        try: iter(ids)
        except TypeError: ids = [ids]
        ids.extend("a")
        if default:
            ids.extend("d")
        statstr = str()
        for ID in ids:
            if ID == "a":
                fitter = self.spectra.workFit.fitter
                statstr += "active fitter: \n"
            elif ID == "d":
                fitter = self.spectra.defaultFitter
                statstr += "default fitter: \n"
            else:
                spec = self.spectra.GetActiveObject()
                if spec is None:
                    continue
                fitter = spec.dict[ID].fitter
                statstr += "fitter status of fit id %d: \n" % ID
            statstr += "Background model: polynomial, deg=%d\n" % fitter.bgdeg
            statstr += "Peak model: %s\n" % fitter.peakModel.name
            statstr += "\n"
            statstr += fitter.OptionsStr()
            statstr += "\n\n"
        hdtv.ui.msg(statstr)
        
        
    def SetFitterParameter(self, parname, status, ids = None, default = False):
        """
        Sets status of fitter parameter
        
        If not specified otherwise only the fitter of the workFit will be changed.
        If default=True, also the default fitter will be changed,
        if a list of fits is given, we try to set the parameter status also 
        for these fits. Be aware that failures for the fits from the list will
        be silently ignored.
        """
        # default fit
        if default:
            try:
                self.spectra.defaultFitter.SetParameter(parname, status)
            except ValueError, msg:
                hdtv.ui.error("while editing default Fit: \n\t%s" % msg)
        # active fit
        fit = self.spectra.workFit
        try:
            fit.fitter.SetParameter(parname, status)
            fit.Refresh()
        except ValueError, msg:
            hdtv.ui.error("while editing active Fit: \n\t%s" % msg)
        # fit list
        if not ids:   # works for None and empty list
            return
        spec = self.spectra.GetActiveObject()
        if spec is None:
            hdtv.ui.warn("No active spectrum")
        try: iter(ids)
        except TypeError: ids=[ids]
        for ID in ids:
            try:
                fit = spec.dict[ID]
                fit.fitter.SetParameter(parname, status)
                fit.Refresh()
            except KeyError:
                pass
 
    def ResetFitterParameters(self, ids=None, default = False):
        """
        Reset Status of Fitter
        
        The fitter of the workFit is resetted to the status of the defaultFitter.
        If default is True, the defaultFitter is resetted to the internal default 
        values first. If a list with ids is given, they are treated in the same 
        way as the workFit.
        """
        if default:
            self.spectra.defaultFitter.ResetParamStatus()
        # active Fit
        fit = self.spectra.workFit
        fit.fitter = copy.copy(self.spectra.defaultFitter)
        fit.Refresh()
        # fit list
        if not ids:  # works for None and empty list
            return
        spec = self.spectra.GetActiveObject()
        if spec is None:
            hdtv.ui.warn("No active spectrum")
        try: iter(ids)
        except TypeError: ids=[ids]
        for ID in ids:
            fit = spec.dict[ID]
            fit.fitter= copy.copy(self.spectra.defaultFitter)
            fit.Refresh() 
            
    def SetPeakModel(self, peakmodel, ids=None, default = False):
        """
        Set the peak model (function used for fitting peaks)
        
        If default is True, the peak model of the default fitter is also set.
        If a list of ids is given, the peak model of the stored fits with that 
        ids will be set. Note, that the latter will fail silently for invalid 
        fit ids.
        """
        # default
        if default:
            self.spectra.defaultFitter.SetPeakModel(peakmodel)
        # active fit
        fit = self.spectra.workFit
        fit.fitter.SetPeakModel(peakmodel)
        fit.Refresh()
        # fit list
        if not ids:   # works for None and empty list
            return
        spec = self.spectra.GetActiveObject()
        if spec is None:
            hdtv.ui.warn("No active spectrum")
        try: iter(ids)
        except TypeError: ids=[ids]
        for ID in ids:
            fit = spec.dict[ID]
            fit.fitter.SetPeakModel(peakmodel)
            fit.Refresh()
       
class TvFitInterface:
    """
    TV style interface for fitting
    """
    def __init__(self, fitInterface):
        self.fitIf = fitInterface
        self.spectra = self.fitIf.spectra  
        
        # Register configuration variables for fit list
        opt = hdtv.options.Option(default = "ID")
        hdtv.options.RegisterOption("fit.list.sort_key", opt) 
                
        prog = "fit execute"
        description = "(re)fit a fit"
        usage = "%prog [OPTIONS] <fit-ids>"
        parser = hdtv.cmdline.HDTVOptionParser(prog = prog, description = description, usage = usage)
        parser.add_option("-s", "--spectrum", action = "store", default = "active",
                            help = "Spectra to work on")
        parser.add_option("-b", "--background", action = "store_true", default = False,
                            help = "fit only the background")
        parser.add_option("-q","--quick", action="store", default=None,
                            help = "set position for doing a quick fit")
        hdtv.cmdline.AddCommand(prog, self.FitExecute, level=0, parser = parser)
        # the "fit execute" command is registered with level=0, 
        # this allows "fit execute" to be abbreviated as "fit", 
        # register all other commands starting with fit with default or higher priority
        
        prog = "fit marker"
        description = "set/delete a marker"
        description +="(possible types are background, region, peak)"
        usage = "%prog type action position"
        parser = hdtv.cmdline.HDTVOptionParser(prog = prog, description = description, usage = usage)
        hdtv.cmdline.AddCommand(prog, self.FitMarkerChange, nargs=3,
                                parser = parser, completer=self.MarkerCompleter)
        
        prog = "fit clear"
        description = "clear the active work fit"
        usage = "%prog"
        parser = hdtv.cmdline.HDTVOptionParser(prog = prog, description = description, usage = usage)
        parser.add_option("-b", "--background_only", action="store_true", default = False,
                            help = "clear only background fit, refit peak fit with internal background")
        hdtv.cmdline.AddCommand(prog, self.FitClear, nargs=0, parser = parser)
        
        prog = "fit store"
        description = "store the active work fit to fitlist"
        usage = "%prog"
        parser = hdtv.cmdline.HDTVOptionParser(prog = prog, description = description, usage = usage)
        hdtv.cmdline.AddCommand(prog, self.FitStore, nargs=0, parser = parser)
               
        prog = "fit activate"
        description = "re-activates a fit from the fitlist"
        usage = "%prog ID"
        parser = hdtv.cmdline.HDTVOptionParser(prog = prog, description = description, usage = usage)
        hdtv.cmdline.AddCommand(prog, self.FitActivate, nargs=1, parser = parser)
        
        prog = "fit delete"
        description = "delete fits"
        usage = "%prog <ids>"
        parser = hdtv.cmdline.HDTVOptionParser(prog = prog, description = description, usage = usage)
        parser.add_option("-s", "--spectrum", action = "store", default = "active",
                        help = "spectrum ids to work on")
        hdtv.cmdline.AddCommand(prog, self.FitDelete, minargs = 1, parser = parser)
        
        prog = "fit show"
        description = "display fits"
        usage = "%prog <ids>"
        parser = hdtv.cmdline.HDTVOptionParser(prog = prog, description = description, usage = usage)
        parser.add_option("-s", "--spectrum", action = "store", default = "active",
                        help = "select spectra to work on")
        parser.add_option("-v", "--adjust-viewport", action = "store_true", default = False,
                        help = "adjust viewport to include all fits")
        hdtv.cmdline.AddCommand(prog, self.FitShow, minargs = 1, parser = parser)
        
        prog = "fit hide"
        description = "hide fits"
        usage = "%prog <ids>"
        parser = hdtv.cmdline.HDTVOptionParser(prog = prog, description = description, usage = usage)
        parser.add_option("-s", "--spectrum", action = "store", default = "active",
                        help = "select spectra to work on")
        hdtv.cmdline.AddCommand(prog, self.FitHide, parser = parser)
        
        prog = "fit focus"
        description = "focus on fit with id"
        usage = "%prog [<id>]"
        parser = hdtv.cmdline.HDTVOptionParser(prog = prog, description = description, usage = usage)
        hdtv.cmdline.AddCommand(prog, self.FitFocus, minargs = 0, parser = parser)
        
        prog = "fit list"
        description = "list fit results"
        usage = "%prog"
        parser = hdtv.cmdline.HDTVOptionParser(prog = prog, description = description, usage = usage)
        parser.add_option("-v", "--visible", action = "store_true", default = False,
                        help = "only list visible fit")
        parser.add_option("-k", "--key-sort", action = "store", default = hdtv.options.Get("fit.list.sort_key"),
                        help = "sort by key")
        parser.add_option("-r", "--reverse-sort", action = "store_true", default = False,
                        help = "reverse the sort")
        parser.add_option("-s", "--spectrum", action = "store", default = "active",
                        help = "select spectra to work on")  
        parser.add_option("-f", "--fit", action = "store", default = "all", 
                        help = "specify which fits to list")
        hdtv.cmdline.AddCommand(prog, self.FitList, parser = parser)
        
        prog = "fit parameter"
        description = "show status of fit parameter, reset or set parameter"
        usage = "%prog [OPTIONS] status | reset | parname <valuePeak1>, <valuePeak2>, ..."
        parser = hdtv.cmdline.HDTVOptionParser(prog = prog, description = description, usage = usage)
        parser.add_option("-d", "--default", action = "store_true", default = False,
                            help = "act on default fitter")
        parser.add_option("-f", "--fit", action = "store", default = None,
                            help = "change parameter of selected fit and refit")
        hdtv.cmdline.AddCommand(prog, self.FitParam, completer = self.ParamCompleter,
                                parser = parser, minargs = 1)
                                
        
        prog = "fit function peak activate"
        description = "selects which peak model to use"
        usage = "%prog [OPTIONS] name"
        parser = hdtv.cmdline.HDTVOptionParser(prog = prog, description = description, usage = usage)
        parser.add_option("-d", "--default", action = "store_true", default = False,
                            help = "change default fitter")
        parser.add_option("-f", "--fit", action = "store", default = None,
                            help = "change selected fits and refit")
        hdtv.cmdline.AddCommand(prog, self.FitSetPeakModel,
                                completer = self.PeakModelCompleter,
                                parser = parser, minargs = 1)
        
        

    def FitMarkerChange(self, args, options):
        """
        Set or delete a marker from command line
        """
        # first argument is marker type name
        mtype = args[0]
        # complete markertype if needed
        mtype = self.MarkerCompleter(mtype)
        if len(mtype)==0:
            hdtv.ui.error("Markertype %s is not valid" %args[0])
            return
        # second argument is action
        action = args[1]
        action = self.MarkerCompleter(action, args=args[0:1])
        if len(action)==0:
            hdtv.ui.error("Invalid action: %s" %args[1])
        # parse position
        try:
            pos = float(args[2])
        except ValueError:
            hdtv.ui.error("Invalid position argument")
            return
        mtype = mtype[0].strip()
        # replace "background" with "bg" which is internally used
        if mtype == "background": mtype="bg"
        action = action[0].strip()
        if action == "set":
            self.spectra.SetMarker(mtype, pos)
        if action == "delete":
            self.spectra.RemoveMarker(mtype, pos)


    def MarkerCompleter(self, text, args=[]):
        """
        Helper function for FitMarkerChange
        """
        if not args:
            mtypes = ["background","region", "peak"]
            return hdtv.cmdhelper.GetCompleteOptions(text, mtypes)
        elif len(args)==1:
            actions = ["set", "delete"]
            return hdtv.cmdhelper.GetCompleteOptions(text, actions)
        
            
    def FitExecute(self, args, options):
        """
        Execute a fit
        """
        try:
            specIDs = hdtv.cmdhelper.ParseIds(options.spectrum, self.spectra)
        except ValueError:
            return "USAGE"
        if len(specIDs) == 0:
            hdtv.ui.warn("No spectrum to work on")
            return
        if options.background:
            doPeaks = False
        else:
            doPeaks = True
        for specID in specIDs:
            try:
                fitIDs = hdtv.cmdhelper.ParseIds(args, self.spectra.dict[specID])
            except ValueError:
                return "USAGE"
            if len(fitIDs) == 0:
                if specID==self.spectra.activeID:
                    if options.quick is not None:
                        try:
                            pos = float(options.quick)
                        except:
                            hdtv.ui.error("Invalid position for quick fit.")
                            return
                        self.fitIf.QuickFit(pos)
                    else:
                        self.spectra.ExecuteFit(peaks=doPeaks) 
                else:
                    hdtv.ui.warn("No fit for spectrum %s to work on." %specID)
            for fitID in fitIDs:
                try:    
                    self.fitIf.ExecuteRefit(specID=specID, fitID=fitID, peaks=doPeaks)
                except KeyError, e:
                    hdtv.ui.warn(e)
                    continue
                
    def FitClear(self, args, options):
        """
        Clear work fit
        """
        self.spectra.ClearFit(options.background_only)
        
        
    def FitStore(self, args, options):
        """
        Store work fit
        """
        if len(args)==1:
            try:
                ID = int(args[0])
            except ValueError:
                return "USAGE"
        else:
            ID=None
        self.spectra.StoreFit(ID)
        
        
    def FitActivate(self, args, options):
        """
        Activate a fit
        
        This marks a stored fit as active and copies its markers to the work Fit
        """
        sid = self.spectra.activeID
        if sid is None:
            hdtv.ui.warn("No active spectrum")
            return
        spec = self.spectra.dict[sid]
        try:
            ids = hdtv.cmdhelper.ParseIds(args, spec)
        except ValueError:
            return "USAGE"
        if len(ids) == 1:
            hdtv.ui.msg("Activating fit %s" %ids[0])
            self.spectra.ActivateFit(ids[0], sid)
        elif len(ids) == 0:
            hdtv.ui.msg("Deactivating fit")
            self.spectra.ActivateFit(None, sid)
        else:
            hdtv.ui.error("Can only activate one fit")


    def FitDelete(self, args, options):
        """ 
        Delete fits
        """
        try:
            sids = hdtv.cmdhelper.ParseIds(options.spectrum, self.spectra)
        except ValueError:
            return "USAGE"
        if len(sids)==0:
            hdtv.ui.warn("No spectra chosen or active")
            return
        else:
            for s in sids:
                spec = self.spectra.dict[s]
                try:
                    ids = hdtv.cmdhelper.ParseIds(args, spec)
                except ValueError:
                    return "USAGE"
                for ID in ids:
                    spec.Pop(ID)

    def FitHide(self, args, options):
        """
        Hide Fits
        """
        # FitHide is the same as FitShow, except that the spectrum selection is inverted
        self.FitShow(args, options, inverse=True)
    
    def FitShow(self, args, options, inverse=False):
        """
        Show Fits
        
        inverse = True inverses the fit selection i.e. FitShow becomes FitHide
        """
        try:
            sids = hdtv.cmdhelper.ParseIds(options.spectrum, self.spectra)
        except ValueError:
            return "USAGE"
        for sid in sids:
            spec = self.spectra.dict[sid]
            try:
                fitIDs = hdtv.cmdhelper.ParseIds(args, spec)
            except ValueError:
                return "USAGE"
            if inverse:
                spec.HideObjects(fitIDs)
            else:
                spec.ShowObjects(fitIDs)
                if options.adjust_viewport:
                    fits = [spec.dict[ID] for ID in fitIDs]
                    self.spectra.window.FocusObjects(fits)
                
    def FitFocus(self, args, options):
        """
        Focus a fit. 
        
        If no fit is given focus the active fit.
        """
        spec = self.spectra.GetActiveObject()
        if spec is None:
            hdtv.ui.error("There is no active spectrum")
            return
        
        assert self.spectra.activeID in self.spectra.visible, "Active objects should always be visible"
        
        fits = list()
        if len(args) == 0:
            fits.append(self.spectra.workFit)
            activeFit = spec.GetActiveObject()
            if activeFit is not None:
                fit.append(activeFit)
        else:
            try:
                ids = hdtv.cmdhelper.ParseIds(args, spec)
            except ValueError:
                return "USAGE"
            fits = [spec.dict[ID] for ID in ids]
            spec.ShowObjects(ids, clear=False)
        if len(fits)==0:
            hdtv.ui.warn("Nothing to focus")
            return
        self.spectra.window.FocusObjects(fits)

 
    def FitList(self, args, options):
        """
        Show a nice table with the results of fits
        
        By default the result of the work fit is shown.
        """
        self.fitIf.PrintWorkFit()
        try:
            sids = hdtv.cmdhelper.ParseIds(options.spectrum, self.spectra)
        except ValueError:
            return "USAGE"
        if len(sids)==0:
            hdtv.ui.warn("No spectra chosen or active")
            return
        # parse sort_key
        key_sort = options.key_sort.lower()
        for sid in sids:
            spec = self.spectra.dict[sid]
            try:
                ids = hdtv.cmdhelper.ParseIds(options.fit, spec)
            except ValueError:
                return "USAGE"
            if options.visible:
                ids = [ID for ID in spec.visible]
            if len(ids)==0:
                continue
            self.fitIf.ListFits(sid, ids, sortBy=key_sort,reverseSort=options.reverse_sort)
            
                
    def FitSetPeakModel(self, args, options):
        """
        Defines peak model to use for fitting
        """
        name = args[0].lower()
        # complete the model name if needed
        models = self.PeakModelCompleter(name)
        # check for unambiguity
        if len(models)>1:
            hdtv.ui.error("Peak model name '%s' is ambiguous" %name)
        if len(models)==0:
            hdtv.ui.error("Invalid peak model '%s'" %name)
        else:
            name = models[0]
            name = name.strip()
            ids = list()
            if options.fit:
                spec = self.spectra.GetActiveObject()
                if spec is None:
                    hdtv.ui.warn("No active spectrum, no action taken.")
                    return
                try:
                    ids = hdtv.cmdhelper.ParseFitIds(options.fit, spec)
                except ValueError:
                    return "USAGE"
            self.fitIf.SetPeakModel(name, ids, options.default)

    def PeakModelCompleter(self, text, args=None):
        """
        Helper function for FitSetPeakModel
        """
        return hdtv.cmdhelper.GetCompleteOptions(text, hdtv.peakmodels.PeakModels.iterkeys())

    def FitParam(self, args, options):
        """
        Manipulate the status of fitter parameter
        """
        # first argument is parameter name
        param = args.pop(0)
        # complete the parameter name if needed
        parameter = self.ParamCompleter(param)
        # check for unambiguity
        if len(parameter)>1:
            hdtv.ui.error("Parameter name %s is ambiguous" %param)
            return
        if len(parameter)==0:
            hdtv.ui.error("Parameter name %s is not valid" %param)
            return
        param = parameter[0]
        param = param.strip()
        ids =list()
        if options.fit:
            spec = self.spectra.GetActiveObject()
            if spec is None:
                hdtv.ui.warn("No active spectrum, no action taken.")
                return
            try:
                ids = hdtv.cmdhelper.ParseIds(options.fit, spec)
            except ValueError:
                return "USAGE"
        if param=="status":
            self.fitIf.ShowFitterStatus(ids, options.default)
        elif param == "reset":
            self.fitIf.ResetFitterParameters(ids, options.default)
        else:
            try:
                self.fitIf.SetFitterParameter(param, " ".join(args), ids, options.default)
            except ValueError, msg:
                hdtv.ui.error(msg)
        
    def ParamCompleter(self, text, args=None):
        """
        Creates a completer for all possible parameter names 
        or valid states for a parameter (args[0]: parameter name).
        If the different peak models are used for active fitter and default fitter,
        options for both peak models are presented to the user.
        """
        if not args:
            params = set(["status", "reset"])
            defaultParams = set(self.spectra.defaultFitter.params)
            activeParams  = set(self.spectra.workFit.fitter.params)
            # create a list of all possible parameter names
            params = params.union(defaultParams).union(activeParams)
            return hdtv.cmdhelper.GetCompleteOptions(text, params)
        else:
            param = args[0]
            states = set()
            # valid states for param in default fitter
            defaultPM = self.spectra.defaultFitter.peakModel
            try:
                defaultStates = set(defaultPM.fValidParStatus[param])
                if len(defaultStates)>1:
                    states.update(defaultStates)
            except KeyError:
                # param is not a parameter of the peak model of the default fitter
                pass
            # valid states for param in active fitter
            activePM = self.fitIf.workFit.fitter.peakModel
            try:
                activeStates = activePM.fValidParStatus[param]
                if len(activeStates)>1:
                    states.update(activeStates)
            except KeyError:
                # param is not a parameter of the peak model of active fitter
                pass
            # remove <type: float> option
            states.discard(float)
            return hdtv.cmdhelper.GetCompleteOptions(text, states)
            
    def ResetFit(self, args, options):
        """
        Reset fitter of a fit to unfitted default.
        """
        try:
            specIDs = hdtv.cmdhelper.ParseIds(options.spectrum, self.spectra)
        except ValueError:
            return "USAGE"
        if len(specIDs) == 0:
            hdtv.ui.error("No spectrum to work on")
            return
        for specID in specIDs:
            try:
                fitIDs = hdtv.cmdhelper.ParseIds(args, self.spectra.dict[specID])
            except ValueError:
                return "USAGE"
            if len(fitIDs) == 0:
                hdtv.ui.warn("No fit for spectrum %d to work on", specID)
                continue
            for fitID in fitIDs:    
                self.fitIf.FitReset(specID=specID, fitID=fitID, resetFitter=not options.keep_fitter)

# plugin initialisation
import __main__
__main__.f = FitInterface(__main__.spectra)


