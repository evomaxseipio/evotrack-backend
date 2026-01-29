# 🚀 Guía de Migración Flutter - Nuevo Formato de Autenticación

## 📋 Cambios en la Respuesta de Autenticación

### Estructura Anterior (ANTES)
```dart
{
  "user": {
    "id": "...",
    "email": "...",
    "first_name": "...",
    "last_name": "...",
    "timezone": "UTC",
    "is_active": true,
    "created_at": "..."
  },
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Estructura Nueva (AHORA)
```dart
{
  "user": {
    "id": "...",
    "email": "...",
    "first_name": "...",
    "last_name": "...",
    "full_name": "John Doe",              // ← NUEVO
    "timezone": "UTC",
    "is_active": true,
    "has_organization": true,               // ← NUEVO
    "organizations": [                     // ← NUEVO (array)
      {
        "id": "org-uuid",
        "name": "Acme Corporation",
        "slug": "acme-corporation",
        "role": "owner"                    // "owner", "admin", "manager", "employee"
      }
    ],
    "created_at": "...",
    "updated_at": "..."
  },
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 🎯 Lógica de Navegación Requerida

### Reglas de Decisión:

1. **Usuario SIN organizaciones** (`has_organization: false` o `organizations.length == 0`)
   - → Redirigir a pantalla de **crear/unión a organización**

2. **Usuario con 1 organización**
   - → Ir directamente al **dashboard** con esa organización

3. **Usuario con múltiples organizaciones Y es owner de 2 o más**
   - → Mostrar **pantalla de selección** para elegir organización

4. **Usuario con múltiples organizaciones pero NO es owner de 2 o más**
   - → Ir directamente al **dashboard** con la primera organización donde es owner (si existe), o la primera disponible

---

## 📱 Implementación Flutter

### 1. Actualizar Modelos de Datos

```dart
// models/organization_basic.dart
class OrganizationBasic {
  final String id;
  final String name;
  final String slug;
  final String role; // "owner", "admin", "manager", "employee"

  OrganizationBasic({
    required this.id,
    required this.name,
    required this.slug,
    required this.role,
  });

  factory OrganizationBasic.fromJson(Map<String, dynamic> json) {
    return OrganizationBasic(
      id: json['id'] as String,
      name: json['name'] as String,
      slug: json['slug'] as String,
      role: json['role'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'slug': slug,
      'role': role,
    };
  }

  bool get isOwner => role == 'owner';
  bool get isAdmin => role == 'admin';
  bool get isManager => role == 'manager';
  bool get isEmployee => role == 'employee';
}

// models/user_response.dart
class UserResponse {
  final String id;
  final String email;
  final String firstName;
  final String lastName;
  final String fullName;              // ← NUEVO
  final String timezone;
  final bool isActive;
  final bool hasOrganization;         // ← NUEVO
  final List<OrganizationBasic> organizations; // ← NUEVO
  final DateTime createdAt;
  final DateTime? updatedAt;

  UserResponse({
    required this.id,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.fullName,            // ← NUEVO
    required this.timezone,
    required this.isActive,
    required this.hasOrganization,     // ← NUEVO
    required this.organizations,       // ← NUEVO
    required this.createdAt,
    this.updatedAt,
  });

  factory UserResponse.fromJson(Map<String, dynamic> json) {
    return UserResponse(
      id: json['id'] as String,
      email: json['email'] as String,
      firstName: json['first_name'] as String,
      lastName: json['last_name'] as String,
      fullName: json['full_name'] as String,  // ← NUEVO
      timezone: json['timezone'] as String,
      isActive: json['is_active'] as bool,
      hasOrganization: json['has_organization'] as bool, // ← NUEVO
      organizations: (json['organizations'] as List<dynamic>?)
          ?.map((org) => OrganizationBasic.fromJson(org as Map<String, dynamic>))
          .toList() ?? [],            // ← NUEVO
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'] as String)
          : null,
    );
  }

  // Helper methods
  int get ownerCount => organizations.where((org) => org.isOwner).length;
  bool get hasMultipleOwnerOrgs => ownerCount >= 2;
  OrganizationBasic? get firstOwnerOrg => 
      organizations.firstWhere((org) => org.isOwner, orElse: () => organizations.first);
}

// models/auth_response.dart
class AuthResponse {
  final UserResponse user;
  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final int expiresIn;

  AuthResponse({
    required this.user,
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
    required this.expiresIn,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      user: UserResponse.fromJson(json['user'] as Map<String, dynamic>),
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      tokenType: json['token_type'] as String,
      expiresIn: json['expires_in'] as int,
    );
  }
}
```

---

### 2. Lógica de Navegación Post-Login

```dart
// services/navigation_service.dart o en tu AuthService
class NavigationService {
  static void handlePostLoginNavigation(
    BuildContext context,
    AuthResponse authResponse,
  ) {
    final user = authResponse.user;

    // Caso 1: Usuario sin organizaciones
    if (!user.hasOrganization || user.organizations.isEmpty) {
      Navigator.pushReplacementNamed(
        context,
        '/onboarding', // o '/create-organization'
      );
      return;
    }

    // Caso 2: Usuario con múltiples organizaciones Y es owner de 2+
    if (user.hasMultipleOwnerOrgs) {
      Navigator.pushReplacementNamed(
        context,
        '/select-organization',
        arguments: user.organizations,
      );
      return;
    }

    // Caso 3: Usuario con 1 organización o múltiples pero solo 1 owner
    // → Ir directamente al dashboard
    final selectedOrg = user.firstOwnerOrg ?? user.organizations.first;
    
    // Guardar organización seleccionada en storage/shared preferences
    _saveSelectedOrganization(selectedOrg);
    
    Navigator.pushReplacementNamed(
      context,
      '/dashboard',
      arguments: {
        'organization': selectedOrg,
        'user': user,
      },
    );
  }

  static Future<void> _saveSelectedOrganization(OrganizationBasic org) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('selected_org_id', org.id);
    await prefs.setString('selected_org_name', org.name);
    await prefs.setString('selected_org_slug', org.slug);
    await prefs.setString('selected_org_role', org.role);
  }
}
```

---

### 3. Pantalla de Selección de Organización

```dart
// screens/select_organization_screen.dart
class SelectOrganizationScreen extends StatelessWidget {
  final List<OrganizationBasic> organizations;

  const SelectOrganizationScreen({
    Key? key,
    required this.organizations,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Filtrar solo las organizaciones donde es owner
    final ownerOrgs = organizations.where((org) => org.isOwner).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Seleccionar Organización'),
        automaticallyImplyLeading: false, // No permitir volver atrás
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Tienes acceso a múltiples organizaciones como propietario. '
              'Selecciona con cuál deseas trabajar:',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 24),
            Expanded(
              child: ListView.builder(
                itemCount: ownerOrgs.length,
                itemBuilder: (context, index) {
                  final org = ownerOrgs[index];
                  return Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: ListTile(
                      leading: CircleAvatar(
                        child: Text(org.name[0].toUpperCase()),
                      ),
                      title: Text(
                        org.name,
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      subtitle: Text('Rol: ${org.role}'),
                      trailing: const Icon(Icons.arrow_forward_ios),
                      onTap: () {
                        _selectOrganization(context, org);
                      },
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _selectOrganization(
    BuildContext context,
    OrganizationBasic organization,
  ) async {
    // Guardar organización seleccionada
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('selected_org_id', organization.id);
    await prefs.setString('selected_org_name', organization.name);
    await prefs.setString('selected_org_slug', organization.slug);
    await prefs.setString('selected_org_role', organization.role);

    // Navegar al dashboard
    Navigator.pushReplacementNamed(
      context,
      '/dashboard',
      arguments: {
        'organization': organization,
      },
    );
  }
}
```

---

### 4. Actualizar Servicio de Autenticación

```dart
// services/auth_service.dart
class AuthService {
  Future<AuthResponse> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final authResponse = AuthResponse.fromJson(data);
      
      // Guardar tokens
      await _saveTokens(authResponse);
      
      return authResponse;
    } else {
      throw Exception('Error en login: ${response.body}');
    }
  }

  Future<AuthResponse> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
        'first_name': firstName,
        'last_name': lastName,
      }),
    );

    if (response.statusCode == 201) {
      final data = jsonDecode(response.body);
      final authResponse = AuthResponse.fromJson(data);
      
      // Guardar tokens
      await _saveTokens(authResponse);
      
      return authResponse;
    } else {
      throw Exception('Error en registro: ${response.body}');
    }
  }

  Future<void> _saveTokens(AuthResponse authResponse) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', authResponse.accessToken);
    await prefs.setString('refresh_token', authResponse.refreshToken);
  }
}
```

---

### 5. Actualizar Pantalla de Login

```dart
// screens/login_screen.dart
class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _authService = AuthService();
  bool _isLoading = false;

  Future<void> _handleLogin(String email, String password) async {
    setState(() => _isLoading = true);

    try {
      final authResponse = await _authService.login(email, password);
      
      // Navegar según la lógica de organizaciones
      NavigationService.handlePostLoginNavigation(context, authResponse);
    } catch (e) {
      // Mostrar error
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    // Tu UI de login existente
    // ...
    // Al hacer login exitoso, llamar _handleLogin()
  }
}
```

---

### 6. Actualizar Rutas

```dart
// main.dart o router.dart
class AppRouter {
  static Route<dynamic> generateRoute(RouteSettings settings) {
    switch (settings.name) {
      case '/login':
        return MaterialPageRoute(builder: (_) => LoginScreen());
      
      case '/select-organization':
        final organizations = settings.arguments as List<OrganizationBasic>;
        return MaterialPageRoute(
          builder: (_) => SelectOrganizationScreen(
            organizations: organizations,
          ),
        );
      
      case '/dashboard':
        return MaterialPageRoute(builder: (_) => DashboardScreen());
      
      case '/onboarding':
        return MaterialPageRoute(builder: (_) => OnboardingScreen());
      
      default:
        return MaterialPageRoute(builder: (_) => LoginScreen());
    }
  }
}
```

---

## 🔄 Flujo Completo de Navegación

```
┌─────────────────┐
│   Login Screen  │
└────────┬────────┘
         │
         ▼
    [Login Success]
         │
         ▼
┌─────────────────────────┐
│  ¿Tiene organizaciones? │
└─────┬───────────┬───────┘
      │ NO         │ SÍ
      ▼            ▼
┌──────────┐  ┌──────────────────────────┐
│Onboarding│  │ ¿Es owner de 2+ orgs?   │
└──────────┘  └─────┬───────────┬───────┘
                    │ SÍ        │ NO
                    ▼            ▼
         ┌──────────────────┐  ┌──────────┐
         │Select Org Screen │  │ Dashboard│
         └────────┬─────────┘  └──────────┘
                  │
                  ▼
            ┌──────────┐
            │ Dashboard│
            └──────────┘
```

---

## ✅ Checklist de Migración

- [ ] Actualizar modelo `UserResponse` con nuevos campos
- [ ] Crear modelo `OrganizationBasic`
- [ ] Actualizar `AuthResponse` para usar nuevo `UserResponse`
- [ ] Implementar lógica de navegación post-login
- [ ] Crear pantalla de selección de organización
- [ ] Actualizar servicio de autenticación
- [ ] Actualizar pantalla de login
- [ ] Agregar rutas nuevas
- [ ] Probar flujo completo:
  - [ ] Usuario sin organizaciones
  - [ ] Usuario con 1 organización
  - [ ] Usuario con múltiples organizaciones (owner de 2+)
  - [ ] Usuario con múltiples organizaciones (solo 1 owner)

---

## 🧪 Casos de Prueba

### Caso 1: Usuario Nuevo (sin organizaciones)
```json
{
  "has_organization": false,
  "organizations": []
}
```
**Resultado esperado:** → Pantalla de onboarding/crear organización

### Caso 2: Usuario con 1 organización
```json
{
  "has_organization": true,
  "organizations": [
    {"id": "1", "name": "Mi Empresa", "slug": "mi-empresa", "role": "owner"}
  ]
}
```
**Resultado esperado:** → Dashboard directamente

### Caso 3: Usuario owner de 2+ organizaciones
```json
{
  "has_organization": true,
  "organizations": [
    {"id": "1", "name": "Empresa A", "slug": "empresa-a", "role": "owner"},
    {"id": "2", "name": "Empresa B", "slug": "empresa-b", "role": "owner"},
    {"id": "3", "name": "Empresa C", "slug": "empresa-c", "role": "admin"}
  ]
}
```
**Resultado esperado:** → Pantalla de selección (solo mostrar Empresa A y B)

### Caso 4: Usuario con múltiples orgs pero solo 1 owner
```json
{
  "has_organization": true,
  "organizations": [
    {"id": "1", "name": "Empresa A", "slug": "empresa-a", "role": "owner"},
    {"id": "2", "name": "Empresa B", "slug": "empresa-b", "role": "admin"}
  ]
}
```
**Resultado esperado:** → Dashboard directamente (con Empresa A)

---

## 📝 Notas Importantes

1. **Campo `full_name`**: Ya no necesitas concatenar `first_name + last_name`, viene directamente en la respuesta
2. **Array de organizaciones**: Siempre viene como array, puede estar vacío `[]`
3. **Rol del usuario**: Viene en cada organización, no a nivel de usuario
4. **Slug de organización**: Úsalo para URLs o identificadores amigables
5. **Persistencia**: Guarda la organización seleccionada en SharedPreferences para usarla en sesiones futuras

---

## 🚀 Comandos Útiles para Testing

```bash
# Probar login con usuario sin organizaciones
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "Pass123"}'

# Probar login con usuario con organizaciones
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "owner@example.com", "password": "Pass123"}'
```

---

¡Listo para implementar! 🎉
