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
"""Signals module."""

from __future__ import annotations

from enum import IntFlag


class signals(IntFlag):
    """HCPh signals with associated bytes values that are sent to BIOPAC."""

    # General events
    RUN = 0x80
    """When a run (e.g., a task fMRI protocol) starts."""
    ET_START_AND_STOP = 0x02
    """Issued when the EyeTracker starts and when it stops recording."""
    ET_START_FIXATION = 0x04
    """For tasks/runs with a fixation point Eye Tracker."""
    ET_STOP_FIXATION = 0x10
    """For tasks/runs with a fixation point Eye Tracker."""

    # QCT events
    QCT_VIS = 0x04
    """Visual block in the QCT."""
    QCT_COG = 0x08
    """Eye tracking block in the QCT."""
    QCT_MOT = 0x10
    """Motor block in the QCT."""
    QCT_BLANK = 0x20
    """Blank block in the QCT."""

    # REST events
    REST_START = 0x20
    """When the resting-state movie starts."""
    REST_STOP = 0x40
    """When the resting-state movie stops."""

    # BHT events
    BHT_IN = 0x04
    """When a breathe-in block starts."""
    BHT_OUT = 0x08
    """When a breathe-out block starts."""
    BHT_HOLD_START_AND_STOP = 0x10
    """When a breath-hold block starts and stops."""

    def to_bytes(self):
        """
        Return bytes from the current value.

        Examples
        --------
        >>> signals.RUN.to_bytes()
        b'\x80'
        >>> (signals.RUN | signals.ET_START_AND_STOP).to_bytes()
        b'\x82'

        """
        return self.value.to_bytes(1, byteorder="big")
