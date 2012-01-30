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

static double
qform(PyArrayObject *v, PyArrayObject *m) {
	int i,j,n;
	double q, c;
	n = v->dimensions[0];
	q = 0;
	for (i=0; i<n;i++) {
		c = 0;
		for (j=0;j<n;j++) {
			c+= *(double *)PyArray_GETPTR2(m, i, j) * *(double *)PyArray_GETPTR1(v, j);
			}
		q+=*(double *) PyArray_GETPTR1(v, i) * c;
	}
	return q;
}

static PyObject *
gicdat_qform(PyObject *self, PyObject *args)
{
	PyArrayObject  *vect, *matr;
	double q;
	PyObject *out;
	if (!PyArg_ParseTuple(args, "OO", &vect, &matr))
			return NULL;
	if (vect == NULL || matr== NULL) return NULL;
	
	if (vect->nd!=1 || matr->nd!=2 || vect->dimensions[0]!=matr->dimensions[0] || vect->dimensions[0]!=matr->dimensions[1])
		{
		return PyErr_Format(PyExc_StandardError,
        					"Qform requires arguments v <array[N]> and m <array[N,N]>");
		goto _fail;					
		}	
	q = qform(vect, matr);
	out = Py_BuildValue("d", q);
	//Py_XINCREF(out);
	return out;
	
	_fail:
		return NULL;
								
}


static PyObject *
gicdat_slidinggauss(PyObject *self, PyObject *args)
{
	PyArrayObject  *dat, *mean, *icov, *offsets, *out, *x;
	int i, j, k, maxoff;
	if (!PyArg_ParseTuple(args, "OOOO", &dat, &mean, &icov, &offsets))
			return NULL;
	if (dat == NULL || mean== NULL || icov==NULL) goto _fail;
	if (dat->nd!=1 || mean->nd!=1 || icov->nd!=2 || mean->dimensions[0]!=icov->dimensions[0] || mean->dimensions[0]!=icov->dimensions[1])
		{
		return PyErr_Format(PyExc_StandardError,
        					"Qform requires arguments dat <array[M], mean <array[N]> and cov <array[N,N]>");
		goto _fail;					
		}	
		
	if (offsets==NULL || offsets==Py_None) {
		offsets = PyArray_Arange(0, mean->dimensions[0], 1, NPY_INT32);
	}
	out = PyArray_ZEROS(1, &dat->dimensions[0], NPY_FLOAT64, 0);
	x = PyArray_ZEROS(1, &mean->dimensions[0], NPY_FLOAT64, 0);
	maxoff = 0;
	for (i=0;i<offsets->dimensions[0];i++) {
		if (*(int *)PyArray_GETPTR1(offsets, i)>maxoff) maxoff = *(int *)PyArray_GETPTR1(offsets, i);
		}
	for (i = maxoff; i<dat->dimensions[0];i++) {
		for (j=0;j<mean->dimensions[0];j++) {
			k = i - *(int *)PyArray_GETPTR1(offsets, j);
			*(double *)PyArray_GETPTR1(x, j)=*(double *)PyArray_GETPTR1(dat, k) -*(double *)PyArray_GETPTR1(mean, j)  ;
			
			}
		*(double *)PyArray_GETPTR1(out, i) = qform(x,icov); 
	
	}
	Py_DECREF(x);
	return out;
	
	_fail:
		return NULL;
								
}

static PyMethodDef slidingmatchMethods[] = {
    {"qform", gicdat_qform, METH_VARARGS,
     "Inputs are a v <array[N]> and m <array[N,N]>. Returns the quadratic form v*m*v' (* indicates matrix product, v is 1D but the ' indicates that it is treated as a row vector in the left position, and a column vector in the right), which is a float"},
	{"sgauss", gicdat_slidinggauss, METH_VARARGS,
	"Inputs are dat <array[M]>, mean <array[N<M]>, icov <array[N,N]>, offsets <array[N] | None>. Return value is <array[M]>, constructed such that at each index i, the value is qform(x - mean, icov), where x is contsrtucted as [ dat[i-offsets[0]], dat[i-offsets[1]..., dat[i-offsets[N-1]] ]. If offsets is None, it defaults to arange(N)"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};
		

PyMODINIT_FUNC
initslidingmatch(void)
{
    import_array();
    (void) Py_InitModule("slidingmatch", slidingmatchMethods);
}

		
