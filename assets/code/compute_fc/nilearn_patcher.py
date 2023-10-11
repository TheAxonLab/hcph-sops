# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# Copyright 2023 The Axon Lab <theaxonlab@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# We support and encourage derived works from this project, please read
# about our expectations at
#
#     https://www.nipreps.org/community/licensing/
#
# STATEMENT OF CHANGES: This file is derived from sources licensed under the BSD
# terms, and this file has been changed.
# The original file this work derives from is found at:
# https://github.com/nilearn/nilearn/blob/main/nilearn/maskers/multi_nifti_maps_masker.py
#
# ORIGINAL WORK'S ATTRIBUTION NOTICE:New BSD License
#
#   Copyright (c) 2007 - 2023 The nilearn developers.
#   All rights reserved.
#
#
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions are met:
#
#     a. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#     b. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#     c. Neither the name of the nilearn developers nor the names of
#        its contributors may be used to endorse or promote products
#        derived from this software without specific prior written
#        permission.
#
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#   ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
#   ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#   DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#   CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
#   OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
#   DAMAGE.
"""Transformer for computing ROI signals of multiple 4D images."""

import itertools

from joblib import Memory, Parallel, delayed

from nilearn._utils import fill_doc
from nilearn._utils.niimg_conversions import _iter_check_niimg
from nilearn.maskers.nifti_maps_masker import NiftiMapsMasker


class MultiNiftiMapsMasker(NiftiMapsMasker):
    """Class for masking of Niimg-like objects.

    MultiNiftiMapsMasker is useful when data from overlapping volumes
    and from different subjects should be extracted (contrary to
    :class:`nilearn.maskers.NiftiMapsMasker`).

    .. note::
        Inf or NaN present in the given input images are automatically
        put to zero rather than considered as missing data.

    Parameters
    ----------
    maps_img : 4D niimg-like object
        See :ref:`extracting_data`.
        Set of continuous maps. One representative time course per map is
        extracted using least square regression.

    mask_img : 3D niimg-like object, optional
        See :ref:`extracting_data`.
        Mask to apply to regions before extracting signals.

    allow_overlap : :obj:`bool`, optional
        If False, an error is raised if the maps overlaps (ie at least two
        maps have a non-zero value for the same voxel). Default=True.
    %(smoothing_fwhm)s
    %(standardize_maskers)s
    %(standardize_confounds)s
    high_variance_confounds : :obj:`bool`, optional
        If True, high variance confounds are computed on provided image with
        :func:`nilearn.image.high_variance_confounds` and default parameters
        and regressed out. Default=False.
    %(detrend)s
    %(low_pass)s
    %(high_pass)s
    %(t_r)s
    dtype : {dtype, "auto"}, optional
        Data type toward which the data should be converted. If "auto", the
        data will be converted to int32 if dtype is discrete and float32 if it
        is continuous.

    resampling_target : {"data", "mask", "maps", None}, optional.
        Gives which image gives the final shape/size:

            - "data" means the atlas is resampled to the shape of the data if
              needed
            - "mask" means the maps_img and images provided to fit() are
              resampled to the shape and affine of mask_img
            - "maps" means the mask_img and images provided to fit() are
              resampled to the shape and affine of maps_img
            - None means no resampling: if shapes and affines do not match,
              a ValueError is raised.

        Default="data".

    %(memory)s
    %(memory_level)s
    %(n_jobs)s
    %(verbose0)s
    reports : :obj:`bool`, optional
        If set to True, data is saved in order to produce a report.
        Default=True.
    %(masker_kwargs)s

    Attributes
    ----------
    maps_img_ : :obj:`nibabel.nifti1.Nifti1Image`
        The maps mask of the data.

    n_elements_ : :obj:`int`
        The number of overlapping maps in the mask.
        This is equivalent to the number of volumes in the mask image.

        .. versionadded:: 0.9.2

    Notes
    -----
    If resampling_target is set to "maps", every 3D image processed by
    transform() will be resampled to the shape of maps_img. It may lead to a
    very large memory consumption if the voxel number in maps_img is large.

    See Also
    --------
    nilearn.maskers.NiftiMasker
    nilearn.maskers.NiftiLabelsMasker
    nilearn.maskers.NiftiMapsMasker

    """

    # memory and memory_level are used by CacheMixin.

    def __init__(
        self,
        maps_img,
        mask_img=None,
        allow_overlap=True,
        smoothing_fwhm=None,
        standardize=False,
        standardize_confounds=True,
        high_variance_confounds=False,
        detrend=False,
        low_pass=None,
        high_pass=None,
        t_r=None,
        dtype=None,
        resampling_target="data",
        memory=Memory(location=None, verbose=0),
        memory_level=0,
        verbose=0,
        reports=True,
        n_jobs=1,
        **kwargs,
    ):
        self.n_jobs = n_jobs
        super().__init__(
            maps_img,
            mask_img=mask_img,
            allow_overlap=allow_overlap,
            smoothing_fwhm=smoothing_fwhm,
            standardize=standardize,
            standardize_confounds=standardize_confounds,
            high_variance_confounds=high_variance_confounds,
            detrend=detrend,
            low_pass=low_pass,
            high_pass=high_pass,
            t_r=t_r,
            dtype=dtype,
            resampling_target=resampling_target,
            memory=memory,
            memory_level=memory_level,
            verbose=verbose,
            reports=reports,
            **kwargs,
        )

    def transform_imgs(self, imgs_list, confounds=None, n_jobs=1, sample_mask=None):
        """Extract signals from a list of 4D niimgs.

        Parameters
        ----------
        %(imgs)s
            Images to process. Each element of the list is a 4D image.
        %(confounds)s
        %(sample_mask)s

        Returns
        -------
        region_signals : list of 2D :obj:`numpy.ndarray`
            List of signals for each map per subject.
            shape: list of (number of scans, number of maps)

        """
        # We handle the resampling of maps and mask separately because the
        # affine of the maps and mask images should not impact the extraction
        # of the signal.

        self._check_fitted()

        niimg_iter = _iter_check_niimg(
            imgs_list,
            ensure_ndim=None,
            atleast_4d=False,
            memory=self.memory,
            memory_level=self.memory_level,
            verbose=self.verbose,
        )

        if confounds is None:
            confounds = itertools.repeat(None, len(imgs_list))

        if sample_mask is None:
            sample_mask = itertools.repeat(None, len(imgs_list))

        func = self._cache(self.transform_single_imgs)

        region_signals = Parallel(n_jobs=n_jobs)(
            delayed(func)(imgs=imgs, confounds=cfs, sample_mask=sms)
            for imgs, cfs, sms in zip(niimg_iter, confounds, sample_mask)
        )
        return region_signals

    def transform(self, imgs, confounds=None, sample_mask=None):
        """Apply mask, spatial and temporal preprocessing.

        Parameters
        ----------
        %(imgs)s
            Images to process. Each element of the list is a 4D image.
        %(confounds)s
        %(sample_mask)s

        Returns
        -------
        region_signals : list of 2D :obj:`numpy.ndarray`
            List of signals for each map per subject.
            shape: list of (number of scans, number of maps)

        """
        self._check_fitted()
        if not hasattr(imgs, "__iter__") or isinstance(imgs, str):
            return self.transform_single_imgs(imgs)
        return self.transform_imgs(
            imgs, confounds, n_jobs=self.n_jobs, sample_mask=sample_mask
        )
