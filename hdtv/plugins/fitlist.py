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
# Write and Read Fitlist saved in xml format
# 
#-------------------------------------------------------------------------------
import os
import glob
import hdtv.cmdline
import hdtv.cmdhelper
import hdtv.fitxml 
import hdtv.ui

import __main__
__main__.fitxml = hdtv.fitxml.FitXml(__main__.spectra)

def WriteFitlist(args, options):
    fname = os.path.expanduser(args[0])
    if not options.force and os.path.exists(fname):
        hdtv.ui.warn("This file already exists:")
        overwrite = None
        while not overwrite in ["Y","y","N","n","","B","b"]:
            question = "Do you want to replace it [y,n] or backup it [B]:"
            overwrite = raw_input(question)
        if overwrite in ["b","B",""]:
            os.rename(fname,"%s.back" %fname)
        elif overwrite in ["n","N"]:
            return 
    sids = hdtv.cmdhelper.ParseIds(options.spectrum, __main__.spectra)
    if len(sids)==0:
        hdtv.ui.error("There is no active spectrum")
        return
    if len(sids)>1:
        hdtv.ui.error("Can only save fitlist of one spectrum")
        return
    __main__.fitxml.WriteFitlist(fname, sids[0])

def ReadFitlist(args, options):
    fnames = list()
    for fname in args:
        fname = os.path.expanduser(fname)
        more = glob.glob(fname)
        if len(more)==0:
            hdtv.ui.warn("no such file %s" %fname)
        fnames.extend(more)
    sids = hdtv.cmdhelper.ParseIds(options.spectrum, __main__.spectra)
    if len(sids)==0:
        hdtv.ui.error("There is no active spectrum")
        return
    for fname in fnames:
        for sid in sids:
            hdtv.ui.msg("Reading fitlist %s to spectrum %s" %(fname, sid))
            __main__.fitxml.ReadFitlist(fname, sid, refit=options.refit)

prog = "fit write"
description = "write fits to xml file"
usage = "%prog filename"
parser = hdtv.cmdline.HDTVOptionParser(prog = prog, description = description, usage = usage)
parser.add_option("-s", "--spectrum", action = "store", default = "active",
                        help = "for which the fits should be saved (default=active)")
parser.add_option("-f","--force",action = "store_true", default=False,
                        help = "overwrite existing files without asking")
hdtv.cmdline.AddCommand(prog, WriteFitlist, nargs=1, fileargs=True, parser=parser)


prog = "fit read"
description = "read fits from xml file"
usage ="%prog filename"
parser = hdtv.cmdline.HDTVOptionParser(prog = prog, description = description, usage = usage)
parser.add_option("-s", "--spectrum", action = "store", default = "active",
                        help = "spectra to which the fits should be added (default=active)")
parser.add_option("-r", "--refit", action = "store_true", default = False,
                        help = "Force refitting during load")
hdtv.cmdline.AddCommand("fit read", ReadFitlist, minargs=1, fileargs=True, parser=parser)


hdtv.ui.msg("loaded fitlist plugin")
