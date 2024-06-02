from .isPrivate import IsPrivate
from .inAdminChat import AdminOrPrivateFilter
from .isAdmin import IsAdmin
from loader import dp

dp.filters_factory.bind(IsPrivate)
dp.filters_factory.bind(AdminOrPrivateFilter)
dp.filters_factory.bind(IsAdmin)

