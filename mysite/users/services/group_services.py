from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from dataclasses import dataclass
from users import selectors


@dataclass
class SendGroupInvitationDto:
    user_id: int

    def __post_init__(self) -> None:
        if not get_user_model().objects.filter(id=self.user_id).exists():
            raise ValidationError(f'Invalid ID {self.user_id}')


class SendGroupInvitation:
    def send(self, user: get_user_model, dto: SendGroupInvitationDto) -> None:
        group = selectors.group_get_by_user_id(user.id)
        user_to_be_invited = selectors.user_get_by_id(dto.user_id)
        if user == user_to_be_invited:
            return
        user_to_be_invited.pending_membership.add(group)


@dataclass
class AcceptGroupInvitationDto:
    group_id: int


class AcceptGroupInvitation:
    def accept(self, user: get_user_model, dto: AcceptGroupInvitationDto):
        pending_groups_ids = selectors.user_get_group_pending_membership(
            user).values_list('id', flat=True)
        if dto.group_id not in pending_groups_ids:
            raise ValidationError(
                f'You were not invited to group with id {dto.group_id}')
        user.membership.add(dto.group_id)
        user.pending_membership.remove(dto.group_id)


@dataclass
class DenyGroupInvitationDto(AcceptGroupInvitationDto):
    pass


class DenyGroupInvitation:
    def deny(self, user: get_user_model, dto: DenyGroupInvitationDto) -> None:
        user.pending_membership.remove(dto.group_id)


@dataclass
class LeaveGroupDto(AcceptGroupInvitationDto):
    pass


class LeaveGroup:
    def leave(self, user: get_user_model, dto: LeaveGroupDto) -> None:
        if user.own_group.id == dto.group_id:
            raise ValidationError('You cannot leave your own group!')
        user.membership.remove(dto.group_id)
