#include <Python.h>
#include <numpy/arrayobject.h>
#include <math.h>
#include <stdio.h>

#define C_ARRAY NPY_ALIGNED | NPY_CONTIGUOUS | NPY_FORCECAST
/*
Copyright (C) 2005-2006 Graham I Cummins
This program is free software; you can redistribute it and/or modify it under 
the terms of the GNU General Public License as published by the Free Software 
Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY 
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with 
this program; if not, write to the Free Software Foundation, Inc., 59 Temple 
Place, Suite 330, Boston, MA 02111-1307 USA
*/

static float min3(float x1, float x2, float x3)
{
    float least;
    least=x1;
    if (x2<least) least=x2;
    if (x3<least) least=x3;
    return least;
}

static long 
intat(PyObject *seq, int ind) {
	return PyInt_AsLong(PySequence_GetItem(seq, ind));
}

static float
victorDist(PyObject *d1, PyObject *d2, float cost)
{
	float dist=0.0;
	float last=1.0;
	float *lasti;
	int i,j, dl1, dl2;
	dl1 =(int)PySequence_Length(d1); 
	dl2 =(int)PySequence_Length(d2); 
	if (dl1== 0) {
		return (float)dl2;
	} else if (dl2 ==0) {
		return (float)dl1;
	}
	lasti=(float *)malloc((dl2+1)*sizeof(float));
	for (i=0;i<dl2+1;i++) {
		lasti[i]=i;
	}
	for (i=1;i<dl1+1; i++) {
		if (i>1) lasti[dl2]=last;
		last=i;
		for (j=1;j<dl2+1;j++) {
			dist=min3(lasti[j]+1, last+1, lasti[j-1]+cost*abs(intat(d1, i-1) - intat(d2, j-1)));
			lasti[j-1]=last;
			last=dist;
		}
	}	
	free(lasti);
	return dist;
}

static PyObject *
gicdat_vpdist(PyObject *self, PyObject *args)
{
	PyObject *idata, *idata2;
	float distance, cost;
	if (!PyArg_ParseTuple(args, "OOf", &idata, &idata2, &cost))
			return NULL;
	distance=victorDist(idata, idata2, cost);
	return Py_BuildValue("f", distance);
}

static PyObject *
gicdat_vpdistM(PyObject *self, PyObject *args)
{
	PyObject *strains;
	PyArrayObject *distances;
	int i, j;
	long n, rshape[2];
	float cost, d;
	if (!PyArg_ParseTuple(args, "Of", &strains, &cost))
			return NULL;
	n = (long)PySequence_Length(strains);
	rshape[0] = n;
	rshape[1] = n;
	distances = PyArray_ZEROS(2, rshape, NPY_FLOAT64, 0);
	Py_INCREF(distances);
	for (i=0;i<n-1;i++) {
		for (j=i+1;j<n;j++) {
			d = victorDist(PySequence_GetItem(strains, i), PySequence_GetItem(strains, j), cost);
			*(double *)PyArray_GETPTR2(distances, i, j) = d; 
			*(double *)PyArray_GETPTR2(distances, j, i) = d;
		}
	}
	return distances;
}


static PyObject *
gicdat_vpdistS(PyObject *self, PyObject *args)
{
	PyObject *itrains, *jtrains;
	PyArrayObject *distances;
	int i, j;
	long rshape[2];
	float cost, d;
	if (!PyArg_ParseTuple(args, "OOf", &itrains, &jtrains, &cost))
			return NULL;
	rshape[0] = (long)PySequence_Length(itrains);
	rshape[1] = (long)PySequence_Length(jtrains);
	distances = PyArray_ZEROS(2, rshape, NPY_FLOAT64, 0);
	Py_INCREF(distances);
	for (i=0;i<rshape[0];i++) {
		for (j=0;j<rshape[1];j++) {
			d = victorDist(PySequence_GetItem(itrains, i), PySequence_GetItem(jtrains, j), cost);
			*(double *)PyArray_GETPTR2(distances, i, j) = d; 
		}
	}
	return distances;
}


static PyMethodDef eventtrainsMethods[] = {
    {"vpdist", gicdat_vpdist, METH_VARARGS,
     "Calculates the Victor/Purpura spike train distance between two event sequences. Inputs are two tuples of ints, followed by a float number. The tuples contain the sample indexes of occurance of events in the two sequences, and the float is the cost of moving an event by one sample, expressed as a fraction of the cost of deleting or adding an event. The return value is a float, which is the computed distance."},
	 {"vpdistMatrix", gicdat_vpdistM, METH_VARARGS,
	  "Calculates a symmetric array of Victor/Purpura spike distances. Input is an N-tuple of tuples of int, and a float. Each tuple of ints is an event sequence (as described in vpdist), and the float is a shift cost (also as described in vpdist). The return value is a symmetric array such that r[i,j] is the Victor distance between elements i and j of the first input." 
	 },
	 {"vpdistSet", gicdat_vpdistS, METH_VARARGS,
	  "Calculates an NxM array of Victor/Purpura spike distances. Input is an N-tuple of tuples of int, an M-tuple of tuples of int, and a float. Each tuple of ints is an event sequence (as described in vpdist), and the float is a shift cost (also as described in vpdist). The return value is an array r such that r[i,j] is the Victor distance between element i of the first tupule, and element j of the second." 
	 },
	 {NULL, NULL, 0, NULL}        /* Sentinel */
};
		

PyMODINIT_FUNC
initeventtrains(void)
{
    import_array();
    (void) Py_InitModule("eventtrains", eventtrainsMethods);
}

		
