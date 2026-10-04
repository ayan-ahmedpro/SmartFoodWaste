from typing import Any

import jwt

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.config import (
    JWT_ALGORITHM,
    JWT_SECRET,
)

from app.data.store import (
    users,
    donations,
)

from app.services.ai_service import (
    ai_service,
)

from app.services.matching_service import (
    matching_service,
)

from app.services.logistics_service import (
    logistics_service,
)

from app.services.request_service import (
    get_request_by_id,
)


router = APIRouter(
    prefix="/api/ai",
    tags=["AI"],
)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
):
    try:
        return jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )


def _serialize_donation(
    donation,
) -> dict[str, Any]:
    """
    Convert a donation model into the verified information
    required by the Coordinator AI.
    """

    return {
        "id": donation.id,
        "donor_id": donation.donor_id,
        "food_name": donation.food_name,
        "category": donation.category,
        "quantity": donation.quantity,
        "reserved_quantity": donation.reserved_quantity,
        "unit": donation.unit,
        "preparation_datetime": str(
            donation.preparation_datetime
        ),
        "safe_consumption_deadline": str(
            donation.safe_consumption_deadline
        ),
        "pickup_address": donation.pickup_address,
        "latitude": donation.latitude,
        "longitude": donation.longitude,
        "storage_instructions": (
            donation.storage_instructions
        ),
        "dietary_information": (
            donation.dietary_information
        ),
        "description": donation.description,
        "status": donation.status,
    }


def _serialize_request(
    request,
) -> dict[str, Any]:
    """
    Convert a request model into the verified information
    required by the Coordinator AI.
    """

    return {
        "id": request.id,
        "donation_id": request.donation_id,
        "organization_id": request.organization_id,
        "requested_quantity": (
            request.requested_quantity
        ),
        "collection_time": (
            request.collection_time
        ),
        "message": request.message,
        "status": request.status,
        "created_at": str(
            request.created_at
        ),
    }


def _serialize_user(
    user,
) -> dict[str, Any]:
    """
    Convert a user model into safe information for the
    Coordinator AI.

    Passwords and authentication information are never
    passed to the AI.
    """

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "status": user.status,
    }


@router.post("/food-analysis")
def analyze_food(
    data: dict,
    current_user=Depends(get_current_user),
):
    required_fields = [
        "food_name",
        "category",
        "quantity",
        "unit",
        "preparation_datetime",
        "safe_consumption_deadline",
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in data
    ]

    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "Required fields are missing."
                ),
                "missing_fields": missing_fields,
            },
        )

    try:
        result = ai_service.analyze_food(
            food_name=str(
                data.get(
                    "food_name",
                    "",
                )
            ),
            category=str(
                data.get(
                    "category",
                    "",
                )
            ),
            quantity=int(
                data.get(
                    "quantity",
                    0,
                )
            ),
            unit=str(
                data.get(
                    "unit",
                    "",
                )
            ),
            preparation_datetime=str(
                data.get(
                    "preparation_datetime",
                    "",
                )
            ),
            safe_consumption_deadline=str(
                data.get(
                    "safe_consumption_deadline",
                    "",
                )
            ),
            storage_instructions=str(
                data.get(
                    "storage_instructions",
                    "",
                )
            ),
            dietary_information=str(
                data.get(
                    "dietary_information",
                    "",
                )
            ),
            description=str(
                data.get(
                    "description",
                    "",
                )
            ),
        )

        return result

    except (
        ValueError,
        TypeError,
    ) as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.post("/match-explanation")
def explain_match(
    data: dict,
    current_user=Depends(get_current_user),
):
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400,
            detail=(
                "Request body must be a JSON object."
            ),
        )

    donation = data.get(
        "donation"
    )

    organization = data.get(
        "organization"
    )

    if not isinstance(
        donation,
        dict,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "The 'donation' field must be "
                "an object."
            ),
        )

    if not isinstance(
        organization,
        dict,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "The 'organization' field must be "
                "an object."
            ),
        )

    try:
        result = matching_service.explain_match(
            donation=donation,
            organization=organization,
        )

        return result

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to generate the "
                "match explanation."
            ),
        ) from error


@router.post(
    "/collection-suggestion"
)
def suggest_collection(
    data: dict,
    current_user=Depends(get_current_user),
):
    """
    Generate an AI logistics suggestion for
    an organization's donation request.

    The backend obtains the actual donation,
    request, organization, quantity, collection
    time, address, and distance.

    AI only explains these verified facts.
    """

    if current_user.get("role") != "organization":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only organizations can request "
                "collection suggestions."
            ),
        )

    if not isinstance(
        data,
        dict,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Request body must be a JSON object."
            ),
        )

    request_id = data.get(
        "request_id"
    )

    if not request_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "The 'request_id' field is required."
            ),
        )

    organization_id = current_user.get(
        "user_id"
    )

    try:
        collection_information = (
            logistics_service.get_collection_information(
                request_id=str(
                    request_id
                ),
                organization_id=str(
                    organization_id
                ),
            )
        )

        donation = collection_information[
            "donation"
        ]

        organization = collection_information[
            "organization"
        ]

        ai_result = ai_service.suggest_collection(
            donation=donation,
            organization=organization,
            collection_information=(
                collection_information[
                    "logistics_facts"
                ]
            ),
        )

        return {
            "success": True,
            "data": {
                "logistics": collection_information[
                    "logistics_facts"
                ],
                "ai": ai_result,
            },
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to generate the "
                "collection suggestion."
            ),
        ) from error


@router.post("/coordinate")
def coordinate_donation_workflow(
    data: dict,
    current_user=Depends(get_current_user),
):
    """
    Generate an AI summary of the current donation workflow.

    The backend gathers the verified donation, request,
    organization, and donor information.

    The Coordinator AI only explains the current workflow.
    It does not perform workflow actions.
    """

    if current_user.get("role") != "organization":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only organizations can request "
                "workflow coordination summaries."
            ),
        )

    if not isinstance(
        data,
        dict,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Request body must be a JSON object."
            ),
        )

    request_id = data.get(
        "request_id"
    )

    if not request_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "The 'request_id' field is required."
            ),
        )

    organization_id = current_user.get(
        "user_id"
    )

    try:
        request = get_request_by_id(
            str(request_id)
        )

        if request is None:
            raise ValueError(
                "Request not found."
            )

        if request.organization_id != organization_id:
            raise ValueError(
                "You are not authorized to access "
                "this request."
            )

        donation = next(
            (
                donation
                for donation in donations
                if donation.id == request.donation_id
            ),
            None,
        )

        if donation is None:
            raise ValueError(
                "Donation not found."
            )

        organization = next(
            (
                user
                for user in users
                if user.id == request.organization_id
                and user.role == "organization"
            ),
            None,
        )

        if organization is None:
            raise ValueError(
                "Organization not found."
            )

        donor = next(
            (
                user
                for user in users
                if user.id == donation.donor_id
                and user.role == "donor"
            ),
            None,
        )

        if donor is None:
            raise ValueError(
                "Donor not found."
            )

        donation_data = _serialize_donation(
            donation
        )

        request_data = _serialize_request(
            request
        )

        organization_data = _serialize_user(
            organization
        )

        donor_data = _serialize_user(
            donor
        )

        workflow_facts = {
            "request_status": request.status,
            "donation_status": donation.status,
            "requested_quantity": (
                request.requested_quantity
            ),
            "donation_quantity": (
                donation.quantity
            ),
            "reserved_quantity": (
                donation.reserved_quantity
            ),
            "collection_time": (
                request.collection_time
            ),
            "request_created_at": str(
                request.created_at
            ),
            "safe_consumption_deadline": str(
                donation.safe_consumption_deadline
            ),
        }

        result = ai_service.coordinate(
            donation=donation_data,
            request=request_data,
            organization=organization_data,
            donor=donor_data,
            workflow_facts=workflow_facts,
        )

        return {
            "success": True,
            "data": {
                "request_id": request.id,
                "request_status": request.status,
                "donation_status": donation.status,
                "ai": result,
            },
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to generate the "
                "workflow coordination summary."
            ),
        ) from error