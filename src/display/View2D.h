/*
 * HDTV - A ROOT-based spectrum analysis software
 *  Copyright (C) 2006-2008  Norbert Braun <n.braun@ikp.uni-koeln.de>
 *
 * This file is part of HDTV.
 *
 * HDTV is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2 of the License, or (at your
 * option) any later version.
 *
 * HDTV is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
 * for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with HDTV; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
 * 
 */

/* View2D: Class implementing a scrollable matrix display */
#ifndef __View2D_h__
#define __View2D_h__

#include <map>
#include <stdint.h>
#include <TGStatusBar.h>
#include <TH2.h>
#include <math.h>
#include "View.h"

namespace HDTV {
namespace Display {

class View2D : public View {
  public:
    View2D(const TGWindow *p, UInt_t w, UInt_t h, TH2 *mat);
    ~View2D();
    Pixmap_t RenderTile(int xoff, int yoff);
    Pixmap_t GetTile(int x, int y);
    void FlushTiles();
    void WeedTiles();
    void DoRedraw();
    void Update();
    void UpdateStatusBar();
    void ZoomFull(Bool_t update=true);
    void ZoomAroundCursor(double f, Bool_t update=true);
    double Log(double x);
    inline void SetStatusBar(TGStatusBar *sb)
      { fStatusBar = sb; }
    
    Bool_t HandleKey(Event_t *ev);
    
    /* Copied from GSViewport: Merge? */
    Bool_t HandleMotion(Event_t *ev);
    Bool_t HandleButton(Event_t *ev);
    Bool_t HandleCrossing(Event_t *ev);
    
    inline int XTileToCh(int x)
       { return (int) ceil(((double) x) / fXZoom - 0.5); }
    inline int YTileToCh(int y)
       { return (int) ceil(((double) y) / fYZoom - 0.5); }
    inline int XScrToTile(int x)
       { return x - fXTileOffset; }
    inline int YScrToTile(int y)
       { return -y + fYTileOffset; }
    inline int XScrToCh(int x)
       { return XTileToCh(XScrToTile(x)); }
    inline int YScrToCh(int y)
       { return YTileToCh(YScrToTile(y)); }
    inline int ZCtsToScr(double z)
       { return (int) (((z - fZOffset) / fZVisibleRegion) * cZColorRange); }
    /* inline void SetXVisibleRegion(double xreg)
       { fXZoom = (double) fWidth / xreg; }
    inline void SetYVisibleRegion(double yreg)
       { fYZoom = (double) fHeight / yreg; } */
    void ShiftOffset(int dX, int dY);
    inline int GetTileId(int pos)
       { return pos < 0 ? (pos / cTileSize) - 1 : pos / cTileSize; }

    void ZtoRGB(int z, int &r, int &g, int &b);
    int GetValueAtPixel(int xs, int ys);
    
  ClassDef(View2D, 1)
  
  protected:
    std::map<uint32_t, Pixmap_t> fTiles;
    double fXZoom, fYZoom;
    double fZVisibleRegion, fZOffset;
    Bool_t fLogScale;
    
    TH2 *fMatrix;
    double fMatrixMax;
    
    int fXTileOffset, fYTileOffset;
    int fXNumTiles, fYNumTiles;
    
    TGStatusBar *fStatusBar;
    
    static const int cZColorRange = 5 * 256;
    static const int cTileSize = 128;
};

} // end namespace Display
} // end namespace HDTV

#endif