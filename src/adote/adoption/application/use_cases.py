from dataclasses import dataclass

from adote.adoption.domain import (
    AccountId,
    AdoptionProcess,
    AdoptionRequest,
    PetId,
    RequestId,
    RequestNotFoundError,
)
from adote.shared.application import Clock

from .ports import AdoptionProcesses, Notifier


@dataclass(frozen=True, slots=True)
class _Changes:
    processes: AdoptionProcesses
    notifier: Notifier
    clock: Clock

    def _publish(self, process: AdoptionProcess) -> AdoptionProcess:
        for event in process.events:
            self.notifier.notify(event)
        return process

    def _pet_of(self, request_id: RequestId) -> PetId:
        pet_id = self.processes.pet_of(request_id)
        if pet_id is None:
            raise RequestNotFoundError
        return pet_id


@dataclass(frozen=True, slots=True)
class RequestAdoption(_Changes):
    def __call__(self, pet_id: PetId, *, adopter_id: AccountId, message: str = "") -> AdoptionRequest:
        """Raises `UnknownPetError`, `OwnPetError`, `PetAlreadyAdoptedError` or `AlreadyRequestedError`."""
        at = self.clock.now()
        process = self._publish(
            self.processes.change(pet_id, lambda p: p.request(adopter_id=adopter_id, message=message, at=at))
        )
        created = process.live_request_of(adopter_id)
        assert created is not None  # noqa: S101 - the process just raised it
        return created


@dataclass(frozen=True, slots=True)
class ApproveRequest(_Changes):
    def __call__(self, request_id: RequestId, *, by: AccountId) -> AdoptionProcess:
        """Raises `RequestNotFoundError`, `NotTheOwnerError` or `RequestNotPendingError`."""
        at = self.clock.now()
        pet_id = self._pet_of(request_id)
        return self._publish(self.processes.change(pet_id, lambda p: p.approve(request_id, by=by, at=at)))


@dataclass(frozen=True, slots=True)
class RejectRequest(_Changes):
    def __call__(self, request_id: RequestId, *, by: AccountId) -> AdoptionProcess:
        """Raises `RequestNotFoundError`, `NotTheOwnerError` or `RequestNotPendingError`."""
        at = self.clock.now()
        pet_id = self._pet_of(request_id)
        return self._publish(self.processes.change(pet_id, lambda p: p.reject(request_id, by=by, at=at)))


@dataclass(frozen=True, slots=True)
class WithdrawRequest(_Changes):
    def __call__(self, request_id: RequestId, *, by: AccountId) -> AdoptionProcess:
        """Raises `RequestNotFoundError`, `NotTheAdopterError` or `RequestNotPendingError`."""
        at = self.clock.now()
        pet_id = self._pet_of(request_id)
        return self._publish(self.processes.change(pet_id, lambda p: p.withdraw(request_id, by=by, at=at)))
