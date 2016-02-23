from django.test import TestCase
from phone.models import *

import hashlib

def encrypt_pwd(pwd, tel, salt='lindyang'):
    pwd = '%s%s%s' %(pwd, tel, salt)
    return hashlib.md5(pwd).hexdigest()

# Create your tests here.

class UserTestCase(TestCase):
    def version(self):
        u0 = User.objects.get(tel='13591141132')
        self.assertEqual(u0.version, '1')

