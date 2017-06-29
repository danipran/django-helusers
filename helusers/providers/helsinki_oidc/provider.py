from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class HelsinkiOIDCAccount(ProviderAccount):
    def get_profile_url(self):
        return self.account.extra_data.get('html_url')

    def get_avatar_url(self):
        return self.account.extra_data.get('avatar_url')

    def to_str(self):
        dflt = super(HelsinkiOIDCAccount, self).to_str()
        return self.account.extra_data.get('name', dflt)


class HelsinkiOIDCProvider(OAuth2Provider):
    id = 'helsinki_oidc'
    name = 'City of Helsinki employees (OIDC)'
    package = 'helusers.providers.helsinki_oidc'
    account_class = HelsinkiOIDCAccount

    def extract_uid(self, data):
        return str(data['sub'])

    def extract_common_fields(self, data):
        return data.copy()

    def get_default_scope(self):
        return ['openid profile email']


providers.registry.register(HelsinkiOIDCProvider)


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        # Update some fields based on profile data.
        field_map = {
            'given_name': 'first_name',
            'family_name': 'last_name',
            'email': 'email',
        }
        update_fields = []
        data = sociallogin.account.extra_data
        user = sociallogin.user
        user_fields = [f.name for f in user._meta.fields]
        for token_attr, user_attr in field_map.items():
            if user_attr not in user_fields:
                continue
            val = getattr(user, user_attr)
            if token_attr not in data or data[token_attr] == val:
                continue

            setattr(user, user_attr, data[token_attr])
            update_fields.append(user_attr)
        if update_fields:
            user.save(update_fields=update_fields)

        ad_groups = data.get('ad_groups', None)
        # Only update AD groups if it's a list of non-empty strings
        if isinstance(ad_groups, list) and \
                all([isinstance(x, str) and len(x) for x in ad_groups]):
            user.update_ad_groups(ad_groups)

        return

    def populate_user(self, request, sociallogin, data):
        user = sociallogin.user
        exclude_fields = ['is_staff', 'password', 'is_superuser']
        user_fields = [f.name for f in user._meta.fields if f not in exclude_fields]
        for field in user_fields:
            if field in data:
                setattr(user, field, data[field])
        return user