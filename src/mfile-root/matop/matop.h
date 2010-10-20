/*
 * Copyright (c) 1992-2008, Stefan Esser <se@ikp.uni-koeln.de>
 * All rights reserved.
 * 
 * Redistribution and use in source and binary forms, with or without modification, 
 * are permitted provided that the following conditions are met:
 * 
 *      * Redistributions of source code must retain the above copyright notice, 
 *        this list of conditions and the following disclaimer.
 *      * Redistributions in binary form must reproduce the above copyright notice, 
 *        this list of conditions and the following disclaimer in the documentation 
 *        and/or other materials provided with the distribution.
 *
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND 
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
 * IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, 
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, 
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE 
 * OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED 
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/* 
 * This code was derived from the matop package, the license of which is
 * reproduced above.
 *
 * Adapted for HDTV by Norbert Braun, 2010.
 */

#ifndef __MATOP_H__
#define __MATOP_H__

#define MBUFSIZE 16*1024*1024	/* 16 MByte Buffer for Symm. und Transpose */

#define MAT_OP_NONE	0
#define MAT_CONV	1
#define MAT_SYMM	2
#define MAT_TRANS	3
#define MAT_PROJ	4
#define MAT_SUM		5
#define MAT_SUB		6
#define MAT_POLY	7
#define MAT_MINMAX	8
#define MAT_FILE	9
#define MAT_STAT	10

#endif