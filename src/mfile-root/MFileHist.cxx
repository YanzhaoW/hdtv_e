#include <TArrayD.h>
#include "MFileHist.h"

MFileHist::MFileHist()
{
	fHist = NULL;
	fInfo = NULL;
}

MFileHist::~MFileHist()
{
	delete fInfo;
	
	if(fHist)
		mclose(fHist);
}

int MFileHist::Open(char *fname)
{
    fHist = mopen(fname, "r");
    if(!fHist)
    	return kFailure;

	fInfo = new minfo;

    if( mgetinfo(fHist, fInfo) != 0 ) {
		delete fInfo;
		fInfo = NULL;
		
		mclose(fHist);
		fHist = NULL;
		        
        return kFailure;
    }
    
    return kSuccess;
}

int MFileHist::Close()
{
	int stat = kSuccess;

	delete fInfo;
	fInfo = NULL;
	
	if(fHist)
		stat = mclose(fHist);
	fHist = NULL;
	
	return stat;
}

template <class histType>
histType *MFileHist::ToTH1(const char *name, const char *title, int level, int line)
{
	histType *hist;

	if(!fHist || !fInfo)
		return NULL;
	if(level >= fInfo->levels || line >= fInfo->lines)
		return NULL;
		
	hist = new histType(name, title, fInfo->columns, -0.5, (double) fInfo->columns - 0.5);
	
	if(!FillTH1(hist, level, line)) {
		delete hist;
		return NULL;
	}
	
	return hist;
}

TH1 *MFileHist::FillTH1(TH1 *hist, int level, int line)
{
	if(!fHist || !fInfo)
		return NULL;
	if(level >= fInfo->levels || line >= fInfo->lines)
		return NULL;
		
	TArrayD buf(fInfo->columns);

    if(mgetdbl(fHist, buf.GetArray(), level, line, 0, fInfo->columns) != fInfo->columns)
    	return NULL;
    
	for(int i=0; i < fInfo->columns; i++) {
		hist->SetBinContent(i+1, buf[i]);
	}
	
	return hist;
}

TH1D *MFileHist::ToTH1D(const char *name, const char *title, int level, int line)
{
	return ToTH1<TH1D>(name, title, level, line);
}

TH1I *MFileHist::ToTH1I(const char *name, const char *title, int level, int line)
{
	return ToTH1<TH1I>(name, title, level, line);
}

double *MFileHist::FillBuf1D(double *buf, int level, int line)
{
	if(!fHist || !fInfo)
		return NULL;
	if(level >= fInfo->levels || line >= fInfo->lines)
		return NULL;
		
	if(mgetdbl(fHist, buf, level, line, 0, fInfo->columns) != fInfo->columns)
       	return NULL;
    
    return buf;
}

TH2 *MFileHist::FillTH2(TH2 *hist, int level)
{
	int line, col;

	if(!fHist || !fInfo)
		return NULL;
	if(level >= fInfo->levels)
		return NULL;
		
	TArrayD buf(fInfo->columns);

	for(line=0; line < fInfo->lines; line++) {
	    if(mgetdbl(fHist, buf.GetArray(), level, line, 0, fInfo->columns) != fInfo->columns)
			break;
    
		for(col=0; col < fInfo->columns; col++) {
			hist->SetBinContent(col+1, line+1, buf[col]);
		}
	}
	
	return line == fInfo->lines ? hist : NULL;
}

template <class histType>
histType *MFileHist::ToTH2(const char *name, const char *title, int level)
{
	histType *hist;

	if(!fHist || !fInfo)
		return NULL;
	if(level >= fInfo->levels)
		return NULL;
		
	hist = new histType(name, title,
						fInfo->columns, -0.5, (double) fInfo->columns - 0.5,
						fInfo->lines, -0.5, (double) fInfo->lines - 0.5);
	
	if(!FillTH2(hist, level)) {
		delete hist;
		return NULL;
	}
	
	return hist;
}

TH2D *MFileHist::ToTH2D(const char *name, const char *title, int level)
{
	return ToTH2<TH2D>(name, title, level);
}

TH2I *MFileHist::ToTH2I(const char *name, const char *title, int level)
{
	return ToTH2<TH2I>(name, title, level);
}