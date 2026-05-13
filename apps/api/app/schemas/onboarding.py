from pydantic import BaseModel, Field


class BlockSetupItem(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)
    floors: int = Field(ge=1, le=99, description="Kat sayısı")
    flats_per_floor: int = Field(ge=1, le=99, description="Kat başına daire sayısı")
    # Daire numarası: {code}{floor}{daire_no} → A101, A102 veya sadece 101, 102
    unit_prefix: str = Field(default="", max_length=10, description="Daire no öneki, boş bırakılırsa blok kodu kullanılır")


class ChargeTemplateItem(BaseModel):
    charge_type: str = Field(min_length=1, max_length=100, description="Örn: aidat, yakıt")
    amount: float = Field(gt=0)
    period: str = Field(min_length=6, max_length=7, description="Örn: 2026-05")
    due_date: str = Field(description="Vade tarihi: YYYY-MM-DD")


class OnboardingSetupRequest(BaseModel):
    blocks: list[BlockSetupItem] = Field(min_length=1, max_length=20)
    charge_template: ChargeTemplateItem | None = Field(
        default=None,
        description="Oluşturulan tüm dairelere uygulanacak borç şablonu (opsiyonel)",
    )


class BlockSummary(BaseModel):
    id: str
    name: str
    code: str
    flats_created: int


class OnboardingSetupResult(BaseModel):
    blocks_created: int
    flats_created: int
    charges_created: int
    blocks: list[BlockSummary]
    message: str
