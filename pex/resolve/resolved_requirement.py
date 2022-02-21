# Copyright 2022 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import absolute_import

import hashlib

from pex.dist_metadata import ProjectNameAndVersion
from pex.pep_440 import Version
from pex.pep_503 import ProjectName
from pex.third_party.pkg_resources import Requirement
from pex.typing import TYPE_CHECKING
from pex.util import CacheHelper

if TYPE_CHECKING:
    from typing import BinaryIO, Iterator, Optional, Tuple

    import attr  # vendor:skip
else:
    from pex.third_party import attr


@attr.s(frozen=True)
class Pin(object):
    @classmethod
    def canonicalize(cls, project_name_and_version):
        # type: (ProjectNameAndVersion) -> Pin
        return cls(
            project_name=ProjectName(project_name_and_version.project_name),
            version=Version(project_name_and_version.version),
        )

    project_name = attr.ib()  # type: ProjectName
    version = attr.ib()  # type: Version

    def as_requirement(self):
        # type: () -> Requirement
        return Requirement.parse(
            "{project_name}=={version}".format(project_name=self.project_name, version=self.version)
        )


@attr.s(frozen=True)
class Fingerprint(object):
    @classmethod
    def from_stream(
        cls,
        stream,  # type: BinaryIO
        algorithm="sha256",  # type: str
    ):
        # type: (...) -> Fingerprint
        digest = hashlib.new(algorithm)
        CacheHelper.update_hash(filelike=stream, digest=digest)
        return cls(algorithm=algorithm, hash=digest.hexdigest())

    algorithm = attr.ib()  # type: str
    hash = attr.ib()  # type: str


@attr.s(frozen=True)
class PartialArtifact(object):
    url = attr.ib()  # type: str
    fingerprint = attr.ib(default=None)  # type: Optional[Fingerprint]


@attr.s(frozen=True)
class ResolvedRequirement(object):
    pin = attr.ib()  # type: Pin
    artifact = attr.ib()  # type: PartialArtifact
    requirement = attr.ib()  # type: Requirement
    additional_artifacts = attr.ib(default=())  # type: Tuple[PartialArtifact, ...]
    via = attr.ib(default=())  # type: Tuple[str, ...]

    def _iter_urls_to_fingerprint(self):
        # type: () -> Iterator[str]
        if not self.artifact.fingerprint:
            yield self.artifact.url
        for artifact in self.additional_artifacts:
            if not artifact.fingerprint:
                yield artifact.url