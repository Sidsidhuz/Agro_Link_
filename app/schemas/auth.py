from pydantic import BaseModel, ConfigDict, Field, model_validator

class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    username: str = Field(min_length=2, max_length=60)
    place: str = Field(default='', max_length=120)
    crops: str = Field(default='', max_length=200)
    about: str = Field(default='', max_length=600)
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)
    irrigation: bool = False

    @model_validator(mode='after')
    def validate_farm(self):
        if len(self.username.strip()) < 2:
            raise ValueError('Name is required')
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError('Provide both coordinates')
        return self

class Register(ProfileUpdate):
    phone: str = Field(min_length=5, max_length=20)
    password: str = Field(min_length=8, max_length=128)

class Login(BaseModel):
    model_config = ConfigDict(extra='forbid')
    phone: str = Field(min_length=5, max_length=20)
    password: str = Field(min_length=1, max_length=128)

class UserPrivate(ProfileUpdate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    phone: str
    avatar: str | None
