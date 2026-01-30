"""Quick test script for platform registry"""
from crawlers.adapters import PlatformRegistry

print("=" * 60)
print("🔍 BDS Platform Registry Test")
print("=" * 60)

platforms = PlatformRegistry.list_platforms()
print(f"\n📋 Registered Platforms ({len(platforms)}):\n")

for p in platforms:
    print(f"  ✅ {p['id']:20} - {p['name']}")

print("\n" + "=" * 60)
print(f"✨ Total: {len(platforms)} platforms ready!")
print("=" * 60)
