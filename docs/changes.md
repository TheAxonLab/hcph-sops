All notable changes to these SOPs are documented below, starting with the most recent version of the document.

!!! note "You found an error"

	If you want to check the list of open issues, please proceed to our [issue tracker](https://github.com/TheAxonLab/hcph-sops/issues).

	If you have identified a problem, a typo, or something missing, and you know it is not in our tracker, please report it by [creating a new issue](https://github.com/TheAxonLab/hcph-sops/issues/new).

<!-- insertion marker -->
## [0.5.0](https://github.com/TheAxonLab/hcph-sops/releases/tag/0.5.0) (June 12, 2026)

<small>[Compare with 0.4.2](https://github.com/TheAxonLab/hcph-sops/compare/0.4.2...0.5.0)</small>

This release consolidates roughly two years of work — the bulk of the HCPh data
collection, the full functional- and structural-connectivity analysis, and a
security-hardened, reproducible documentation build. Changes are grouped by theme; only
milestone pull requests (and a few individual commits) are linked.

### Connectivity analysis & reliability

- Functional-connectivity (FC) estimation and variability analyses, covering sparse
  inverse-covariance estimation and intra-/inter-scanner reliability quantified with the
  intraclass correlation coefficient (ICC) ([#549], [#551], [#553]).
- Bayesian modeling of structural-connectivity (SC) reliability, with a standalone worked
  example ([#528], [#537]).
- FC-matrix loading and confound retrieval refactored into reusable `load_save`/`confounds`
  modules, and mood/state-questionnaire parsing to derive analysis confounds (sleep,
  caffeine, room environment) from the study's issue templates ([#523], [#527], [#557]).

### Generalizability (multi-scanner) protocol

- SOPs for the multi-scanner "generalizability" acquisitions (Prisma / Vida / VidaFit),
  including scanner-specific handling of the alarm screen, audio system, and console
  unlocking, plus standardized protocols and scan durations ([#493], [#495], [#497]).
- Wave-2 recruitment and scheduling adjustments ([#499]).

### Eye-tracking

- End-to-end eye-tracking → BIDS conversion and screening/QC guidance, including a revised
  conversion pipeline and drift handling ([#459]).

### Physiological recordings

- BIOPAC/AcqKnowledge handling and physiological → BIDS conversion, including splitting
  multi-run AcqKnowledge files ([#506]); clarified ECG calibration instructions ([#539]).

### Data management with DataLad

- DataLad-based data management on the Curnagl HPC cluster, derivatives organized as
  subdatasets, and a BIDS indexer driving data intake ([#507], [#522], [#542]).

### Preprocessing on HPC

- fMRIPrep on Curnagl (SLURM): anatomical-only runs, micromamba environments, and
  TemplateFlow pre-download for offline compute nodes ([#508], [#516], [#519]).

### Quality control

- QC/QA criteria for unprocessed and preprocessed data and for functional connectivity, and
  an analysis of the manual image-rating experience ([#469]).

### Manuscript, figures & references

- Registered-report figures and machinery to save figure captions for automatic generation
  of the paper's supplementary material ([#544]); clarified methods (e.g. atlas
  dimensionality vs. number of regions) and a README listing the datasets required to
  reproduce the analyses ([#555], [#559]); a documented data-release checklist ([#538]).

### Site infrastructure, CI & build

- **Security:** removed the compromised `polyfill.io` CDN — sold in 2024 and serving malware
  — from the MathJax configuration ([#562]).
- Modernized and **pinned** the MkDocs/Material stack for reproducible builds, dropped the
  unmaintained `mkpdfs` PDF fork, and pinned the MathJax CDN with Subresource Integrity
  ([#562]); repaired the deploy/codespell CI workflows and fixed broken links and spelling
  ([#550], [#564]).

[#459]: https://github.com/TheAxonLab/hcph-sops/pull/459
[#469]: https://github.com/TheAxonLab/hcph-sops/pull/469
[#493]: https://github.com/TheAxonLab/hcph-sops/pull/493
[#495]: https://github.com/TheAxonLab/hcph-sops/pull/495
[#497]: https://github.com/TheAxonLab/hcph-sops/pull/497
[#499]: https://github.com/TheAxonLab/hcph-sops/pull/499
[#506]: https://github.com/TheAxonLab/hcph-sops/pull/506
[#507]: https://github.com/TheAxonLab/hcph-sops/pull/507
[#508]: https://github.com/TheAxonLab/hcph-sops/pull/508
[#516]: https://github.com/TheAxonLab/hcph-sops/pull/516
[#519]: https://github.com/TheAxonLab/hcph-sops/pull/519
[#522]: https://github.com/TheAxonLab/hcph-sops/pull/522
[#523]: https://github.com/TheAxonLab/hcph-sops/pull/523
[#527]: https://github.com/TheAxonLab/hcph-sops/pull/527
[#528]: https://github.com/TheAxonLab/hcph-sops/pull/528
[#537]: https://github.com/TheAxonLab/hcph-sops/pull/537
[#538]: https://github.com/TheAxonLab/hcph-sops/pull/538
[#539]: https://github.com/TheAxonLab/hcph-sops/pull/539
[#542]: https://github.com/TheAxonLab/hcph-sops/pull/542
[#544]: https://github.com/TheAxonLab/hcph-sops/pull/544
[#549]: https://github.com/TheAxonLab/hcph-sops/pull/549
[#550]: https://github.com/TheAxonLab/hcph-sops/pull/550
[#551]: https://github.com/TheAxonLab/hcph-sops/pull/551
[#553]: https://github.com/TheAxonLab/hcph-sops/pull/553
[#555]: https://github.com/TheAxonLab/hcph-sops/pull/555
[#557]: https://github.com/TheAxonLab/hcph-sops/pull/557
[#559]: https://github.com/TheAxonLab/hcph-sops/pull/559
[#562]: https://github.com/TheAxonLab/hcph-sops/pull/562
[#564]: https://github.com/TheAxonLab/hcph-sops/pull/564

## [0.4.2](https://github.com/TheAxonLab/hcph-sops/releases/tag/0.4.2) (September 27, 2023)

<small>[Compare with 0.4.1](https://github.com/TheAxonLab/hcph-sops/compare/0.4.1...0.4.2)</small>

### Bug fixes

- CITATION.cff ([f36b24a](https://github.com/TheAxonLab/hcph-sops/commit/f36b24a1daa9a993ad0dbe7ca1c2f888e7c45a05) by Oscar Esteban).
- Trying to hold my temper with Zenodo ([c118518](https://github.com/TheAxonLab/hcph-sops/commit/c1185183925905586db8d35d3fd71150854fe9f6) by Oscar Esteban).

## [0.4.1](https://github.com/TheAxonLab/hcph-sops/releases/tag/0.4.1) (September 27, 2023)

<small>[Compare with 0.4.0](https://github.com/TheAxonLab/hcph-sops/compare/0.4.0...0.4.1)</small>

## [0.4.0](https://github.com/TheAxonLab/hcph-sops/releases/tag/0.4.0) (September 27, 2023)

<small>[Compare with 0.3.0](https://github.com/TheAxonLab/hcph-sops/compare/0.3.0...0.4.0)</small>

### Enhancements, new features, and additions

- Add report pre-registered on OSF and fix references
 ([f9a8360](https://github.com/TheAxonLab/hcph-sops/commit/f9a8360efd56e8ab33876b68f0c51012c47f6cb1) by [Oscar Esteban](https://github.com/oesteban)).
- Replace ``--merge true`` with ``--how merge`` in datalad updates
 ([d297d45](https://github.com/TheAxonLab/hcph-sops/commit/d297d45c9f4ab837702b748bb961277fecdf07ac) by [Oscar Esteban](https://github.com/oesteban)).
- Add *DataLad* documentation for synchronizing and adding new data
 ([5d57e74](https://github.com/TheAxonLab/hcph-sops/commit/5d57e7475f5a4a2bf77658fc6ad1c0099324eeb6) by [Oscar Esteban](https://github.com/oesteban)).
- Add a ``.zenodo.json`` with the intent of connecting Zenodo
 ([ee429ea](https://github.com/TheAxonLab/hcph-sops/commit/ee429ea4ef72479fd6b0e8baf5a650f3f20e9a81) by [Oscar Esteban](https://github.com/oesteban)).
- Play nice with Apache license in heuristic, better documentation
 ([2dffffc](https://github.com/TheAxonLab/hcph-sops/commit/2dffffcc8fae8fb4abd4f3c7ed275a9960c41178) by [Oscar Esteban](https://github.com/oesteban)).

### Bug Fixes

- Datalad DOI and link
 ([fc63118](https://github.com/TheAxonLab/hcph-sops/commit/fc6311836865c3b564610601e19d5f917f5602ef) by [Oscar Esteban](https://github.com/oesteban)).
- Escape HTML special characters
 ([e54c468](https://github.com/TheAxonLab/hcph-sops/commit/e54c468b08520de764ba3cf6c8650f3f50bbc204) by [Oscar Esteban](https://github.com/oesteban)).
- Escaping characters
 ([737edce](https://github.com/TheAxonLab/hcph-sops/commit/737edce814c7ca1b4dda1ffee850cce08cdf73fa) by [Oscar Esteban](https://github.com/oesteban)).
- Remaining bugs in heuristic file
 ([443493c](https://github.com/TheAxonLab/hcph-sops/commit/443493c6f91fe59ee9656362253d2d0388456043) by [Oscar Esteban](https://github.com/oesteban)). Related issues/PRs: [#179](https://github.com/TheAxonLab/hcph-sops/issues/179)
- Revise heuristic after testing it
 ([ca49867](https://github.com/TheAxonLab/hcph-sops/commit/ca49867f1712e61cefb0327d91f05e9a966d6013) by [Oscar Esteban](https://github.com/oesteban)).
- Overhaul of the data-management section with DataLad
 ([5afcd97](https://github.com/TheAxonLab/hcph-sops/commit/5afcd97004f96d8314e5eaf034d152d8cf2d1b8d) by [Oscar Esteban](https://github.com/oesteban)). Related issues/PRs: [#100](https://github.com/TheAxonLab/hcph-sops/issues/100), [#163](https://github.com/TheAxonLab/hcph-sops/issues/163), [#160](https://github.com/TheAxonLab/hcph-sops/issues/160)

## [0.3.0](https://github.com/TheAxonLab/hcph-sops/releases/tag/0.3.0) (September 06, 2023)

<small>[Compare with 0.2.0](https://github.com/TheAxonLab/hcph-sops/compare/0.2.0...0.3.0)</small>

### Enhancements, new features, and additions

- Replace unicode symbols with octicons/fontawesome icons
 ([675e1ff](https://github.com/TheAxonLab/hcph-sops/commit/675e1ffc99ee1983d5d5858052cea465363a8db3) by [Oscar Esteban](https://github.com/oesteban)).
- Add ET description to intro
 ([8bf5278](https://github.com/TheAxonLab/hcph-sops/commit/8bf5278d47150d6c4df454c7d8906aec279952b4) by [Oscar Esteban](https://github.com/oesteban)). Related issues/PRs: [#146](https://github.com/TheAxonLab/hcph-sops/issues/146), [#153](https://github.com/TheAxonLab/hcph-sops/issues/153)
- Deep revision of the PR
 ([1fefe2d](https://github.com/TheAxonLab/hcph-sops/commit/1fefe2d98b4b10bb255aa908a544e68bb14fa467) by [Oscar Esteban](https://github.com/oesteban)).
- Added a safety check for the desiccant chamber color
 ([7c13efc](https://github.com/TheAxonLab/hcph-sops/commit/7c13efc30625935bd8c0369174de7a2ea6f53f5f) by [Alexandre Cionca](https://github.com/acionca)).

### Bug Fixes

- Scanner name leak
 ([71a5e81](https://github.com/TheAxonLab/hcph-sops/commit/71a5e81d1e8c3dc4c8bbf8f01d88163870551ae7) by [Alexandre Cionca](https://github.com/acionca)).
- Indentation for rendering / show admonition folded
 ([0747ffe](https://github.com/TheAxonLab/hcph-sops/commit/0747ffe8ebb272e3558f090709faae5d3a89d35b) by [Oscar Esteban](https://github.com/oesteban)).
- Typos ([ae572d9](https://github.com/TheAxonLab/hcph-sops/commit/ae572d919dbd33e3b21b2efbc47a97c250982c79) by [Céline Provins](https://github.com/celprov)).
- Add missing picture in emergency procedures section
 ([e977607](https://github.com/TheAxonLab/hcph-sops/commit/e977607933c444a306639f61431ef99874b8f431) by [Oscar Esteban](https://github.com/oesteban)). Related issues/PRs: [#89](https://github.com/TheAxonLab/hcph-sops/issues/89)

## [0.2.0](https://github.com/TheAxonLab/hcph-sops/releases/tag/0.2.0) (August 29, 2023)

<small>[Compare with 0.1.0](https://github.com/TheAxonLab/hcph-sops/compare/0.1.0...0.2.0)</small>

### Enhancements, new features, and additions

- Change icon of quote admonitions
 ([fbadaed](https://github.com/TheAxonLab/hcph-sops/commit/fbadaedc37d61e2b2f137cede897fd608433142e) by [Oscar Esteban](https://github.com/oesteban)).
- Large overhaul, including initial flowchart of the experiment
 ([0e0d390](https://github.com/TheAxonLab/hcph-sops/commit/0e0d390931ba13b96374a14cf8ea495f782eda85) by [Oscar Esteban](https://github.com/oesteban)).
- Add explanation in SOPs and code to run defacing
 ([2d8982c](https://github.com/TheAxonLab/hcph-sops/commit/2d8982c11368678b7141c31cc575d62eada474e7) by [Céline Provins](https://github.com/celprov)
).
- Add codespell
 ([61717da](https://github.com/TheAxonLab/hcph-sops/commit/61717daacaddc4d2a5cbb60893e1ea3504aa184e) by [Oscar Esteban](https://github.com/oesteban)).
- Add folder structure of the BIDS dataset
 ([c3d0a2a](https://github.com/TheAxonLab/hcph-sops/commit/c3d0a2a01a7bbe2fc953c28c709ceeba2ede6479) by [Oscar Esteban](https://github.com/oesteban)). Related issues/PRs: [#94](https://github.com/TheAxonLab/hcph-sops/issues/94)
- Add tape for head motion
 ([2dbae4d](https://github.com/TheAxonLab/hcph-sops/commit/2dbae4d7c359ef48fc058861708ce6750bfc8ce4) by [Oscar Esteban](https://github.com/oesteban)). Related issues/PRs: [#87](https://github.com/TheAxonLab/hcph-sops/issues/87)
- Add STP100D and MMBT-S manuals
 ([9feb336](https://github.com/TheAxonLab/hcph-sops/commit/9feb3366ad617219f3cbcb8a6fdbe77bbaea382e) by [Oscar Esteban](https://github.com/oesteban)).
- Improve some admonitions
 ([de3f034](https://github.com/TheAxonLab/hcph-sops/commit/de3f034568d4c08684b72bd3f9457c246cb69849) by [Oscar Esteban](https://github.com/oesteban)).

### Bug Fixes

- Stop leaking host name
 ([5a42d85](https://github.com/TheAxonLab/hcph-sops/commit/5a42d8574b6a4b9157f2bbe3bb2445eaef9e6be5) by [Oscar Esteban](https://github.com/oesteban)). Related issues/PRs: [#122](https://github.com/TheAxonLab/hcph-sops/issues/122)
- Refactor of the preliminary section, separating an intro from it
 ([19b4571](https://github.com/TheAxonLab/hcph-sops/commit/19b4571589a49cabd22fa2b092bd7a9ada006c40) by [Oscar Esteban](https://github.com/oesteban)).
- Trim trailing spaces, change admonition type
 ([6e16e80](https://github.com/TheAxonLab/hcph-sops/commit/6e16e80baa13299b57785d46a15599dd8569c044) by [Oscar Esteban](https://github.com/oesteban)).
- Revert removal of indentation in script file
 ([9be8d05](https://github.com/TheAxonLab/hcph-sops/commit/9be8d055b8e21fc3ae56cf6d41d23ad46fd02b3d) by [Oscar Esteban](https://github.com/oesteban)).
- Reorder some incongruent steps, move sound, light and ventilation
 ([e1f4b4b](https://github.com/TheAxonLab/hcph-sops/commit/e1f4b4b35d1bf9db422a10469b26fcdc8be16c7e) by [Oscar Esteban](https://github.com/oesteban)).
- Use octicons and fontawesome
 ([09927cc](https://github.com/TheAxonLab/hcph-sops/commit/09927cc63e16b9cdd5a82d6c566b124e9d78d255) by [Oscar Esteban](https://github.com/oesteban)).
- Inconsistencies in the ET's eye-coverage setting and calibration
 ([15cebe2](https://github.com/TheAxonLab/hcph-sops/commit/15cebe21044daa79d2ce8e04332a9af420b36cf3) by [Oscar Esteban](https://github.com/oesteban)).
- Misplaced ET description and minor revisions
 ([60475e7](https://github.com/TheAxonLab/hcph-sops/commit/60475e7ad21cd4f595beb381dc9a69fc897fdb25) by [Oscar Esteban](https://github.com/oesteban)). Related issues/PRs: [#99](https://github.com/TheAxonLab/hcph-sops/issues/99)
- Spell check and indentation with spaces
 ([2c2cdeb](https://github.com/TheAxonLab/hcph-sops/commit/2c2cdeb979fffecb485def7bc48d70f677f37659) by [Oscar Esteban](https://github.com/oesteban)).
- Add a note regarding disruption on BIDS names after session 14
 ([1da4810](https://github.com/TheAxonLab/hcph-sops/commit/1da4810516dc6a08e6362bef464bb1d0bd150080) by [Oscar Esteban](https://github.com/oesteban)).
- Wrong number of sessions at index page
 ([1adb77d](https://github.com/TheAxonLab/hcph-sops/commit/1adb77de68e241c395f4ccb6dd425b8d655fd96e) by [Oscar Esteban](https://github.com/oesteban)).
- Typo
 ([abe827c](https://github.com/TheAxonLab/hcph-sops/commit/abe827c22b9c5f57fa949a02d7c3eeb42b346f41) by [Oscar Esteban](https://github.com/oesteban)).
- Improve the key listening
 ([ead2438](https://github.com/TheAxonLab/hcph-sops/commit/ead2438129b1898bc2696590ff6d21e446fa3a46) by [Oscar Esteban](https://github.com/oesteban)).

### Maintenance and Continuous Integration

- Update git-changelog config
 ([29d79f0](https://github.com/TheAxonLab/hcph-sops/commit/29d79f07de8ad9ddca3fdbef3f73f96e05633509) by [Oscar Esteban](https://github.com/oesteban)).
- Fix file path and run black for style
 ([164d8f1](https://github.com/TheAxonLab/hcph-sops/commit/164d8f1d7e09528118efa5547dc1c11b0c79ef8a) by [Oscar Esteban](https://github.com/oesteban)).

## [0.1.0](https://github.com/TheAxonLab/hcph-sops/releases/tag/0.1.0) (June 29, 2023)

The first release of these SOPs.
Currently, the document is still a work in progress, with the [Data management](data-management/post-session.md), [Preprocessing](processing/preprocessing.md), and [Release of data](release.md) yet to be written.

<small>[Compare with first commit](https://github.com/TheAxonLab/hcph-sops/compare/51fbd53f255aa8ee25b1ecb38b3429c400fabea3...0.1.0)</small>

### Enhancements, new features, and additions

- Rename study-settings file
 ([f53526e](https://github.com/TheAxonLab/hcph-sops/commit/f53526ecec5cbe26679f8bbcfea134306571cde7) by [Oscar Esteban](https://github.com/oesteban)).
- Add task timings and references
 ([b21c717](https://github.com/TheAxonLab/hcph-sops/commit/b21c7171139a4a19060fc648e41cf1dc019a05e7) by [Oscar Esteban](https://github.com/oesteban)). Related issues/PRs: [#73](https://github.com/TheAxonLab/hcph-sops/issues/73) Co-authored-by: [Elodie Savary](https://github.com/esavary)
- Add *phys2bids* commandline
 ([0d22fd7](https://github.com/TheAxonLab/hcph-sops/commit/0d22fd71d28f59c405b5f01fab18127780be6ea2) by [Oscar Esteban](https://github.com/oesteban)).
- Change theme, add chuv logo, update data-storage
 ([a00e833](https://github.com/TheAxonLab/hcph-sops/commit/a00e83325f02110c0c1a7a3389def10339475115) by [Oscar Esteban](https://github.com/oesteban)).
- Refining the participant preparation
 ([f450fd2](https://github.com/TheAxonLab/hcph-sops/commit/f450fd208ceb83fa0c800be6e71e6231c2a0a25a) by [Oscar Esteban](https://github.com/oesteban)).
- Sectioning the participant preparation
 ([84a4ee1](https://github.com/TheAxonLab/hcph-sops/commit/84a4ee1b6a306fafda8e7c7332db423003986d0b) by [Oscar Esteban](https://github.com/oesteban)).
- Revise [@celprov](https://github.com/celprov)'s code
 ([a011894](https://github.com/TheAxonLab/hcph-sops/commit/a0118947eb563bfdc6e329d73a82abe7702c76c2) by [Oscar Esteban](https://github.com/oesteban)).
- Minimal, stylistic changes
 ([030a9ca](https://github.com/TheAxonLab/hcph-sops/commit/030a9caf7c422e117a4fb4b9f339fa1be7c08d68) by [Oscar Esteban](https://github.com/oesteban)).
- Remove comment about starting recordings as it is now covered by [#71](https://github.com/TheAxonLab/hcph-sops/issues/71)
 ([e4fa2cf](https://github.com/TheAxonLab/hcph-sops/commit/e4fa2cf301ad7b7b8a7f35ddc0a6bb37f412278e) by [Oscar Esteban](https://github.com/oesteban)).
- Overhaul of the scanning section of the SOPs
 ([732c963](https://github.com/TheAxonLab/hcph-sops/commit/732c9632d91a6f537af026227e178d10c48030c7) by [Oscar Esteban](https://github.com/oesteban)).
- Add emergency procedures
 ([fc52766](https://github.com/TheAxonLab/hcph-sops/commit/fc52766e9793ad516155df01d54b57f27f1e94c1) by [Céline Provins](https://github.com/celprov)
).
- Miscalleneous improvements and picture addition
 ([b9b74c0](https://github.com/TheAxonLab/hcph-sops/commit/b9b74c05a5bc697bd8c43cd8513dcb0b057fde53) by [Céline Provins](https://github.com/celprov)
).
- Add info on how to configure the Acknowledge software and record physiolocal signals
 ([f321875](https://github.com/TheAxonLab/hcph-sops/commit/f32187555b9a399b5cafab56530318bd29a38d84) by [Céline Provins](https://github.com/celprov)
).
- Add information about the outputs of the different sequences to better explain the procedure
 ([c7db90a](https://github.com/TheAxonLab/hcph-sops/commit/c7db90a871620e7df2a0f0495e04e024b85936ce) by [Hélène Lajous](https://github.com/helenelajous)).
- Add info about cleaning procedure
 ([f15155a](https://github.com/TheAxonLab/hcph-sops/commit/f15155a5103b53c6f6526d6a9e07aca03f3b0388) by [Hélène Lajous](https://github.com/helenelajous)).
- Correct typos and add info in case you know which exam will be run next
 ([3d82aee](https://github.com/TheAxonLab/hcph-sops/commit/3d82aee5b703eb812e6c23ecd4bca84b05eb173f) by [Hélène Lajous](https://github.com/helenelajous)).
- Add details about how to switch to advanced user mode to save a protocol
 ([8e5c46a](https://github.com/TheAxonLab/hcph-sops/commit/8e5c46a02ea0f725b3e2404329b3428ce31df3a7) by [Hélène Lajous](https://github.com/helenelajous)).
- Add details and correct a few typos
 ([fdd742d](https://github.com/TheAxonLab/hcph-sops/commit/fdd742de2266e0ab2e7aa76252619c52c207c200) by [Hélène Lajous](https://github.com/helenelajous)).
- Review comments
 ([1745329](https://github.com/TheAxonLab/hcph-sops/commit/1745329924878c5dc81b6b7d1697b93029a1f61b) by [Oscar Esteban](https://github.com/oesteban)).
- Add picture of the ET attached
 ([eaa3a8a](https://github.com/TheAxonLab/hcph-sops/commit/eaa3a8a3b7b8a9f6e18ef1b5b469ab04de516fee) by [Oscar Esteban](https://github.com/oesteban)).
- Setup *mkpdfs* plugin
 ([2d6f9fd](https://github.com/TheAxonLab/hcph-sops/commit/2d6f9fd1d7819943adb0312bf397945a0be5ac19) by [Oscar Esteban](https://github.com/oesteban)).
- Make it louder
 ([6d6cce4](https://github.com/TheAxonLab/hcph-sops/commit/6d6cce44cfcd39b00af88617c45a9bebd48050d3) by [Oscar Esteban](https://github.com/oesteban)).
- Add info box about moving the mirror slightly to the right
 ([589fd63](https://github.com/TheAxonLab/hcph-sops/commit/589fd6387dc4c6a35b1a0ec94cbd57c8d3400297) by [Oscar Esteban](https://github.com/oesteban)).
- Add warning about attachment of infrared mirror
 ([00c214d](https://github.com/TheAxonLab/hcph-sops/commit/00c214d26232700293199788b40615422ddab683) by [Oscar Esteban](https://github.com/oesteban)).
- Miscalleneous improvements and image additions
 ([a74aa6d](https://github.com/TheAxonLab/hcph-sops/commit/a74aa6d4989b3bcf600086140fa79788ca53b6cb) by [Céline Provins](https://github.com/celprov)
).
- Give instructions on how to switch on the scanner
 ([c83ad23](https://github.com/TheAxonLab/hcph-sops/commit/c83ad232a763e7aaf7ce427f1ceb98d6d4a3b29e) by [Hélène Lajous](https://github.com/helenelajous)).
- Improve how the scanner is switched off
 ([f95d559](https://github.com/TheAxonLab/hcph-sops/commit/f95d55990c4106d8e6b19b2bf0693ab7536830b7) by [Hélène Lajous](https://github.com/helenelajous)).
- Say you want to turn the key
 ([85180b4](https://github.com/TheAxonLab/hcph-sops/commit/85180b44d3b0d825e245cb3baac8e3da1d9703de) by [Hélène Lajous](https://github.com/helenelajous)).
- [heudiconv heuristic] Do not deduplicate if run is found
 ([5f15cca](https://github.com/TheAxonLab/hcph-sops/commit/5f15ccaf59aa974b56a98de2b94be571e4562e15) by [Oscar Esteban](https://github.com/oesteban)).
- Add phone call script
 ([8b10d1c](https://github.com/TheAxonLab/hcph-sops/commit/8b10d1c96cb8fd1e0bb3a3233e53e329f2443584) by [Céline Provins](https://github.com/celprov)
).
- Add what to do if the alarm rings
 ([f89e399](https://github.com/TheAxonLab/hcph-sops/commit/f89e39977e01aa39866742c66b3ff473182dd586) by [Céline Provins](https://github.com/celprov)
).
- Replace BIOPAC setup photo with Ines' annotated one
 ([8e97af7](https://github.com/TheAxonLab/hcph-sops/commit/8e97af771d0bf7758cf86468d551248e5f8e0d14) by [Céline Provins](https://github.com/celprov)
).
- Add missing bibliography
 ([a667955](https://github.com/TheAxonLab/hcph-sops/commit/a6679559e1f7a604ffda222c73bd4062d04be9d2) by [Céline Provins](https://github.com/celprov)
).
- Addition of miscalleneous information and of many missing pictures
 ([20ad2bd](https://github.com/TheAxonLab/hcph-sops/commit/20ad2bd88603b6e84ca82e045fb9227d12fda17c) by [Céline Provins](https://github.com/celprov)
).
- Add link to reproin
 ([dd4978f](https://github.com/TheAxonLab/hcph-sops/commit/dd4978f5bcc6aa323cbe1e97f5a2986c6760e042) by [Oscar Esteban](https://github.com/oesteban)).
- Add a filter to show missing secrets as REDACTED or replace values
 ([61451c8](https://github.com/TheAxonLab/hcph-sops/commit/61451c847c3553d85c9c406f3df317400314ea69) by [Oscar Esteban](https://github.com/oesteban)).
- Improvements to the data management section
 ([2a176c1](https://github.com/TheAxonLab/hcph-sops/commit/2a176c15d3bba5fc06f177b4b42af7f011de8c2f) by [Oscar Esteban](https://github.com/oesteban)).
- Minimal improvements to clean-up
 ([d20edf3](https://github.com/TheAxonLab/hcph-sops/commit/d20edf3e87360d8dce1280c669edb6bc4559a3de) by [Oscar Esteban](https://github.com/oesteban)).
- Add pictures and improve new exam description
 ([c02291f](https://github.com/TheAxonLab/hcph-sops/commit/c02291f82d784bfa006c101cb20bce8c913851df) by [Oscar Esteban](https://github.com/oesteban)).
- Split data collection
 ([516c388](https://github.com/TheAxonLab/hcph-sops/commit/516c388cb1a38c699eb381b2f0586b617e16b73b) by [Oscar Esteban](https://github.com/oesteban)).
- Add GA video
 ([944a525](https://github.com/TheAxonLab/hcph-sops/commit/944a525880b2263f7c6b6b719fcf7f33f1fe4d3e) by [Oscar Esteban](https://github.com/oesteban)).
- Reorder misplaced steps, improve rendering
 ([3ede838](https://github.com/TheAxonLab/hcph-sops/commit/3ede838775d3437c4fe377e47cf34a4d7e2e38f3) by [Oscar Esteban](https://github.com/oesteban)).
- Ensuring it looks good when rendered
 ([07b0f04](https://github.com/TheAxonLab/hcph-sops/commit/07b0f04bf2298d818b97eb535885f9a4fe33ef02) by [Oscar Esteban](https://github.com/oesteban)).
- Added some files, restructure and fix some items
 ([3fa2c85](https://github.com/TheAxonLab/hcph-sops/commit/3fa2c85215c1881ed84cfa30c357f33847e84a07) by [Oscar Esteban](https://github.com/oesteban)).
- Fix typos and overhaul of data collection
 ([00e3daf](https://github.com/TheAxonLab/hcph-sops/commit/00e3daffd2c844e274f6902220c05263a169c878) by [Oscar Esteban](https://github.com/oesteban)).
- Add images of gas analyzer
 ([6032ed0](https://github.com/TheAxonLab/hcph-sops/commit/6032ed01e4dfe354e8a2d3a59c6a6d5a957247f7) by [Céline Provins](https://github.com/celprov)
).
- Add info how to setup the respiration belt and the gas analyzer
 ([62bf6fd](https://github.com/TheAxonLab/hcph-sops/commit/62bf6fd2c7ab4a26396834432c752ef4cd436775) by [Céline Provins](https://github.com/celprov)
).
- Add info to setup BIOPAC
 ([3719eca](https://github.com/TheAxonLab/hcph-sops/commit/3719eca2529eaa681287c47edafc10f8a37b9850) by [Céline Provins](https://github.com/celprov)
).
- Add info to turn off computer
 ([3e66ec8](https://github.com/TheAxonLab/hcph-sops/commit/3e66ec85861eab28338081da436aa0286a0fa9c8) by [Céline Provins](https://github.com/celprov)
).
- Add info about plugging the coil after the exam has been open
 ([1d5b501](https://github.com/TheAxonLab/hcph-sops/commit/1d5b501d7fd31b85f796ea24c44e15dd772ba1ba) by [Céline Provins](https://github.com/celprov)
).
- Add info about how to save the magnitude image of the fmap
 ([d3efc7d](https://github.com/TheAxonLab/hcph-sops/commit/d3efc7dc2b6eed9e5dd8662fe545d100102f66cb) by [Céline Provins](https://github.com/celprov)
).
- Add ack, edit/reorder some sections
 ([46e41fa](https://github.com/TheAxonLab/hcph-sops/commit/46e41fab015c6bd923a571f05fb69f916f9a10c2) by [Oscar Esteban](https://github.com/oesteban)).
- First pass at data collection checklist
 ([2ab93f7](https://github.com/TheAxonLab/hcph-sops/commit/2ab93f7e3e908f66a28ec124500c57853cf82e37) by [Oscar Esteban](https://github.com/oesteban)).
- Update README
 ([3833e37](https://github.com/TheAxonLab/hcph-sops/commit/3833e370c8d15e8263e34ae66d3a530dec13a2d7) by [Oscar Esteban](https://github.com/oesteban)).

### Bug Fixes

- Add missing settings file
 ([0d4d3f8](https://github.com/TheAxonLab/hcph-sops/commit/0d4d3f8ce7490657f0517595a71103996eb14615) by [Oscar Esteban](https://github.com/oesteban)).
- [heudiconv heuristic] Identify phase and mag in func and fmap-epi
 ([e1e3170](https://github.com/TheAxonLab/hcph-sops/commit/e1e3170d8da31a55d1a7b7cf1b53d9d7ed953844) by [Oscar Esteban](https://github.com/oesteban)).
- [heudiconv heuristic] Robuster detection of phase/mag in GRE fieldmaps
 ([e65f0d2](https://github.com/TheAxonLab/hcph-sops/commit/e65f0d2a6e26dcf3a96d21cce34d9febef727ec6) by [Oscar Esteban](https://github.com/oesteban)).
- Wrong path of mathjax
 ([731dfdd](https://github.com/TheAxonLab/hcph-sops/commit/731dfddd89f49ef5980e7c3da9b3ea77f84e9a14) by [Oscar Esteban](https://github.com/oesteban)).
- Reorder scanning protocol to match sequences order in the manuscript
 ([80ee8f4](https://github.com/TheAxonLab/hcph-sops/commit/80ee8f4002cdd9ed003e9296b11355a2b18582ed) by [Céline Provins](https://github.com/celprov)
).
- Correct console parameter name for reconstruction
 ([dd1f3cf](https://github.com/TheAxonLab/hcph-sops/commit/dd1f3cfff78eb02521b7d73d91a3dc1770eea75f) by [Céline Provins](https://github.com/celprov)
).
- Fix layout
 ([3facec9](https://github.com/TheAxonLab/hcph-sops/commit/3facec988c160ffda362e71df55e6840b886d273) by [Céline Provins](https://github.com/celprov)
).
- Wrong link to *psychopy* git repo
 ([33ed5e5](https://github.com/TheAxonLab/hcph-sops/commit/33ed5e5bc9610bb660f448550903e145da221389) by [Céline Provins](https://github.com/celprov)
).
- Missing picture
 ([7eb7f42](https://github.com/TheAxonLab/hcph-sops/commit/7eb7f42f37d064252f3ee2884d7d1017fc9db0ea) by [Céline Provins](https://github.com/celprov)
).
- Update RR figure 1
 ([387722b](https://github.com/TheAxonLab/hcph-sops/commit/387722b35f7e93a0f67b5dadd32468d2e7e62fa2) by [Oscar Esteban](https://github.com/oesteban)).
- Add missing dependency
 ([976ae4c](https://github.com/TheAxonLab/hcph-sops/commit/976ae4cc269e1d5b82d9dcebf2087912379de9d3) by [Oscar Esteban](https://github.com/oesteban)).
- Correct errors I introduced in [@helenelajous](https://github.com/helenelajous)' PR
 ([3b656f2](https://github.com/TheAxonLab/hcph-sops/commit/3b656f27fe6185b9e1af0c0fc84528895b748d91) by [Oscar Esteban](https://github.com/oesteban)).
- [heudiconv heuristic] More sensible decision for phasediff fieldmaps
 ([3d9b73e](https://github.com/TheAxonLab/hcph-sops/commit/3d9b73e73f6fb4735eb73bfbde084cf1346e9e8a) by [Oscar Esteban](https://github.com/oesteban)).
- [heudiconv heuristic] Set run when duplicates of a sequence are found
 ([504e217](https://github.com/TheAxonLab/hcph-sops/commit/504e2170dc92b607bcfd7d356d6bb5a02cb7f8ca) by [Oscar Esteban](https://github.com/oesteban)).
- [heudiconv heuristic] Overhaul of the reproin heuristic
 ([6576b32](https://github.com/TheAxonLab/hcph-sops/commit/6576b321ec641c1eaea3e0800ea865a37ad8061a) by [Oscar Esteban](https://github.com/oesteban)).
- Minimal amends
 ([9e9d56f](https://github.com/TheAxonLab/hcph-sops/commit/9e9d56f6d8cb0318b3ed382a0e31381f762fb311) by [Oscar Esteban](https://github.com/oesteban)).
- PACSMAN instructions
 ([b562372](https://github.com/TheAxonLab/hcph-sops/commit/b5623725f97e5832e1cb1bcb7da0c91c71cd5ed6) by [Oscar Esteban](https://github.com/oesteban)).
- PACSMAN csv file example
 ([e0a8f66](https://github.com/TheAxonLab/hcph-sops/commit/e0a8f66725c2048235b7ea6a6357e5982890b53f) by [Oscar Esteban](https://github.com/oesteban)).
- Images with wrong paths, and names
 ([5260d62](https://github.com/TheAxonLab/hcph-sops/commit/5260d62d8f455e9ed285f3de233b39ffc6d2b91e) by [Oscar Esteban](https://github.com/oesteban)).
- Miscellaneous stuff
 ([df5a300](https://github.com/TheAxonLab/hcph-sops/commit/df5a300a4f84237ef0607c464b431cca0c3a16b7) by [Oscar Esteban](https://github.com/oesteban)).
- Update version of gha/checkout and fix path second time
 ([cfcc19c](https://github.com/TheAxonLab/hcph-sops/commit/cfcc19c1a8da01f6d07ef4a58b3ac2cbd3bd0383) by [Oscar Esteban](https://github.com/oesteban)).
- Still setting up path
 ([dfe542c](https://github.com/TheAxonLab/hcph-sops/commit/dfe542c96d3b1a064075715c5b7a09f98c29bc49) by [Oscar Esteban](https://github.com/oesteban)).
- Roll-back the path option
 ([ac2661f](https://github.com/TheAxonLab/hcph-sops/commit/ac2661f25f768e27a0b71c6145ca9de2a1fdf333) by [Oscar Esteban](https://github.com/oesteban)).
- Checkout action
 ([1a149b2](https://github.com/TheAxonLab/hcph-sops/commit/1a149b2207ea72118e82e2f664431b5b8185870c) by [Oscar Esteban](https://github.com/oesteban)).
- Remove toc plugin
 ([3861174](https://github.com/TheAxonLab/hcph-sops/commit/38611744407fe9101edce0dfca812b930c2fbaf5) by [Oscar Esteban](https://github.com/oesteban)).

### Maintenance and Continuous Integration

- Set `--in-place` editing of the changelog
 ([48f8acd](https://github.com/TheAxonLab/hcph-sops/commit/48f8acdab772c69d4a7cf1305562958292b4c163) by [Oscar Esteban](https://github.com/oesteban)).
- Refine changelog update with *git-changelog*
 ([e4ea298](https://github.com/TheAxonLab/hcph-sops/commit/e4ea298cddd965c6e01953ded4f0868e4645899f) by [Oscar Esteban](https://github.com/oesteban)).
- Use *git-changelog* to update the changelog
 ([856e58a](https://github.com/TheAxonLab/hcph-sops/commit/856e58a56f14861ce1bce6d9079d26b9e63ca539) by [Oscar Esteban](https://github.com/oesteban)).
- Remove old exemplary code
 ([2e5697c](https://github.com/TheAxonLab/hcph-sops/commit/2e5697cb7c627422db6b5ffb2a71c017f84ef216) by [Oscar Esteban](https://github.com/oesteban)).
