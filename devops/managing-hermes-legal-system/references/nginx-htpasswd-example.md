# Nginx htpasswd Example

## File Location
`/etc/nginx/.htpasswd`

## Format
```
username:$apr1$hash$encrypted_password
```

## Current Users
- `lucien127@proton.me:$apr1$...` (managed by htpasswd)

## Commands

### Creating/Updating a User Password
```bash
sudo htpasswd -bc /etc/nginx/.htpasswd lucien127@proton.me Lucien.489
```
- `-b`: batch mode (password on command line)
- `-c`: create new file (only use for the first user)

### Adding a New User
```bash
sudo htpasswd -b /etc/nginx/.htpasswd newuser newpassword
```

### Deleting a User
```bash
sudo htpasswd -D /etc/nginx/.htpasswd lucien127@proton.me
```

### Verifying the File
```bash
cat /etc/nginx/.htpasswd
```

### Testing the Configuration
```bash
sudo nginx -t
```

### Reloading Nginx
```bash
sudo systemctl reload nginx
```

## Nginx Config Snippet
```nginx
server {
    listen 80;
    server_name zhiyan.dev www.zhiyan.dev;

    location /admin/ {
        auth_basic "智研 Admin Area";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:3001/;
        # ... other proxy settings
    }
}
```