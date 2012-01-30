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

static float eucd(PyArrayObject *a, int row1, int row2)
{
	double d;
    double ds = 0.0;
    int i;
    for (i=0;i<a->dimensions[1];i++) {
    	d =*(double *)PyArray_GETPTR2(a, row1, i)
    		-	*(double *)PyArray_GETPTR2(a, row2, i);
    	ds+=d*d;
    }
    return sqrt(ds);
}

static float cbd(PyArrayObject *a, int row1, int row2)
{
	double d;
    double ds = 0.0;
    int i;
    for (i=0;i<a->dimensions[1];i++) {
    	d =*(double *)PyArray_GETPTR2(a, row1, i)
    		-	*(double *)PyArray_GETPTR2(a, row2, i);
    	if (d>0) {
    		ds+=d;
    	} else {
    		ds-= d;
    	}
    }
    return ds;
}
static PyObject *
gicdat_edist(PyObject *self, PyObject *args)
{
	PyArrayObject *inp, *distances;
	int i, j;
	double d;
	long rshape[2];
	if (!PyArg_ParseTuple(args, "O", &inp))
			return NULL;
	rshape[0] = inp->dimensions[0];
	rshape[1] = inp->dimensions[0];
	distances = PyArray_ZEROS(2, rshape, NPY_FLOAT64, 0);
	for (i=0;i<rshape[0]-1;i++) {
		for (j=i;j<rshape[1];j++) {
			d = eucd(inp, i, j);
			*(double *)PyArray_GETPTR2(distances, i, j) = d;
			*(double *)PyArray_GETPTR2(distances, j, i) = d;
		}
	}
	return distances;
}

static PyObject *
gicdat_cbdist(PyObject *self, PyObject *args)
{
	PyArrayObject *inp, *distances;
	int i, j;
	double d;
	long rshape[2];
	if (!PyArg_ParseTuple(args, "O", &inp))
			return NULL;
	rshape[0] = inp->dimensions[0];
	rshape[1] = inp->dimensions[0];
	distances = PyArray_ZEROS(2, rshape, NPY_FLOAT64, 0);
	for (i=0;i<rshape[0]-1;i++) {
		for (j=i;j<rshape[1];j++) {
			d = cbd(inp, i, j);
			*(double *)PyArray_GETPTR2(distances, i, j) = d;
			*(double *)PyArray_GETPTR2(distances, j, i) = d;
		}
	}
	return distances;
}
static PyMethodDef distanceMethods[] = {
    {"edist", gicdat_edist, METH_VARARGS,
     "Calculates the matrix of all pairwise euclidean distances between the rows of its argument (a 2D array)"
     },
     {"cbdist", gicdat_cbdist, METH_VARARGS,
      "Calculates the matrix of all pairwise city block distances between the rows of its argument (a 2D array)"
      },
	 {NULL, NULL, 0, NULL}        /* Sentinel */
};
		

PyMODINIT_FUNC
initdistance(void)
{
    import_array();
    (void) Py_InitModule("distance", distanceMethods);
}

		
