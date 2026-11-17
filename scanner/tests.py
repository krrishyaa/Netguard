import json
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import ScanLog


class AuthenticationFlowTests(TestCase):
    def test_user_can_register_login_and_open_dashboard(self):
        register_url = reverse('register')
        login_url = reverse('login')

        self.assertEqual(self.client.get(register_url).status_code, 200)
        response = self.client.post(register_url, {
            'username': 'normaluser',
            'email': 'normal@example.com',
            'full_name': 'Normal User',
            'password': 'SuperSecure123!',
            'password_confirm': 'SuperSecure123!',
        })
        self.assertRedirects(response, reverse('index'))
        self.assertTrue(User.objects.filter(username='normaluser').exists())

        self.client.logout()
        response = self.client.post(login_url, {
            'username': 'normaluser',
            'password': 'SuperSecure123!',
        })
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(self.client.get(reverse('index')).status_code, 200)

    def test_admin_login_uses_the_same_dashboard(self):
        User.objects.create_superuser('adminuser', 'admin@example.com', 'AdminSecure123!')

        response = self.client.post(reverse('login'), {
            'username': 'adminuser',
            'password': 'AdminSecure123!',
        })

        self.assertRedirects(response, reverse('index'))


class ScannerApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='scanneruser', password='SuperSecure123!')
        self.client.force_login(self.user)

    @patch('scanner.views.get_all_local_ips', return_value={'127.0.0.1'})
    @patch('scanner.views.find_nmap', return_value='nmap')
    @patch('scanner.views.PRIVILEGE_STATUS', {'ok': False, 'warning': ''})
    @patch('scanner.views.subprocess.run')
    def test_scan_uses_connect_mode_and_saves_user_history(
        self, run_scan, _nmap, _local_ips
    ):
        run_scan.return_value = SimpleNamespace(
            returncode=0,
            stdout='PORT   STATE SERVICE\n22/tcp open  ssh\n',
            stderr='',
        )

        response = self.client.post(
            reverse('scan_target'),
            data=json.dumps({'target': '127.0.0.1'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'][0]['port'], 22)
        args = run_scan.call_args.args[0]
        self.assertIn('-sT', args)
        self.assertNotIn('-O', args)
        self.assertFalse(run_scan.call_args.kwargs.get('shell', False))
        log = ScanLog.objects.get(user=self.user)
        self.assertEqual(log.decrypt_data()['target'], '127.0.0.1')

    @patch('scanner.views.subprocess.run')
    def test_scan_rejects_non_ip_targets_without_running_nmap(self, run_scan):
        response = self.client.post(
            reverse('scan_target'),
            data=json.dumps({'target': 'localhost; whoami'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        run_scan.assert_not_called()

    @patch('scanner.views.find_nmap', return_value=None)
    def test_scan_reports_missing_nmap(self, _nmap):
        response = self.client.post(
            reverse('scan_target'),
            data=json.dumps({'target': '127.0.0.1'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn('Nmap was not found', response.json()['error'])
