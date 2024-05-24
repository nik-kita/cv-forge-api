from models.profile_model import Profile
from sqlmodel import Session, select, func
from models.user_model import User
from schemas.profile_schema import ModifyProfileReq, ProfileReq
from fastapi import HTTPException
from src.services import user_service


def gen_default(user: User, session: Session):
    default_profile = Profile(user_id=user.id)
    session.add(default_profile)
    session.commit()
    session.refresh(default_profile)

    return default_profile


def get(*, user_id: int, profile_name: str, session: Session):
    sql_query = select(Profile).where(
        Profile.user_id == user_id,
        Profile.name == profile_name,
    )
    profile = session.exec(sql_query).first()

    return profile


def get_all_public(*, nik: str, session: Session, offset: int = 0, limit: int = 10):
    user = user_service.get_by_nik(nik, session)

    if not user:
        return (False, f"User '{nik}' not found")

    all_private = get_all_own(
        user_id=user.id, session=session, offset=offset, limit=limit)
    all_public = all_private  # TODO

    return all_public


def get_all_own(*, user_id: int, session: Session, offset: int = 0, limit: int = 10):
    sql_query_profiles = select(Profile).where(
        Profile.user_id == user_id
    ).offset(offset).limit(limit)
    sql_query_total = select(func.count()).select_from(Profile).where(
        Profile.user_id == user_id
    )
    total = session.exec(sql_query_total).one()
    profiles = session.exec(sql_query_profiles).all()

    return {
        'items': profiles,
        'total': total,
        'offset': offset,
    }


def delete(*, user_id: int, profile_id: int, session: Session):
    profile = session.get(Profile, profile_id)

    if profile is None:
        raise HTTPException(404, "Profile not found")
    elif profile.user_id != user_id:
        raise HTTPException(403, "Forbidden")

    session.delete(profile)
    session.commit()


def modify(
    *,
    user_id: int,
    profile_id: int,
    session: Session,
    data: ModifyProfileReq,
):
    profile = session.get(Profile, profile_id)

    if profile is None:
        raise HTTPException(404, "Profile not found")
    elif profile.user_id != user_id:
        raise HTTPException(403, "Forbidden")

    profile.name = data.name if data.name else profile.name
    profile.summary = data.summary if data.summary else profile.summary
    profile.details = data.details if data.details else profile.details

    profile.contacts.extend([
        c.pre_upsert(user_id=user_id, profile_id=profile.id, session=session) for c in data.contacts
    ]) if data.contacts else None

    profile.education.extend([
        ed.pre_upsert(user_id=user_id, profile_id=profile.id, session=session) for ed in data.education
    ]) if data.education else None

    profile.experience.extend([
        exp.pre_upsert(user_id=user_id, profile_id=profile.id, session=session) for exp in data.experience
    ]) if data.experience else None

    profile.languages.extend([
        l.pre_upsert(user_id=user_id, profile_id=profile.id, session=session) for l in data.languages
    ]) if data.languages else None

    profile.skills.extend([
        s.pre_upsert(user_id=user_id, profile_id=profile.id, session=session) for s in data.skills
    ]) if data.skills else None

    profile.avatar = data.avatar.pre_upsert(
        user_id=user_id
    ) if data.avatar else profile.avatar

    session.add(profile)
    session.commit()
    session.refresh(profile)

    return profile


def upsert(
    *,
    user_id: int,
    data: ProfileReq,
    session: Session,
):
    profile = get(
        user_id=user_id, profile_name=data.name, session=session
    ) or Profile(
        user_id=user_id,
        name=data.name,
    )

    if not profile.id:
        session.add(profile)
        session.commit()
        session.refresh(profile)

    profile.summary = data.summary

    profile.contacts = [
        c.pre_upsert(user_id=user_id, profile_id=profile.id, session=session) for c in data.contacts
    ] if data.contacts else []

    profile.education = [
        ed.pre_upsert(user_id=user_id, profile_id=profile.id, session=session) for ed in data.education
    ] if data.education else []

    profile.experience = [
        exp.pre_upsert(user_id=user_id, profile_id=profile.id, session=session) for exp in data.experience
    ] if data.experience else []

    profile.languages = [
        l.pre_upsert(user_id=user_id, profile_id=profile.id, session=session) for l in data.languages
    ] if data.languages else []

    profile.skills = [
        s.pre_upsert(user_id=user_id, profile_id=profile.id, session=session) for s in data.skills
    ] if data.skills else []

    profile.avatar = data.avatar.pre_upsert(
        user_id=user_id,
        session=session,
    ) if data.avatar else None

    session.add(profile)
    session.commit()
    session.refresh(profile)

    return profile
