#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::System {
class String;
}

namespace DotNet::UnityEditor {

class EditorPrefs {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit EditorPrefs(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: EditorPrefs(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint8_t (*CallHasKey_4Oa4KGDR__vvaosUsC29xLg)(void* key, void** reinteropException);
  public: static bool HasKey(const ::DotNet::System::String& key);
  private: static void* (*CallGetString_4Oa4KGDR__vvaosUsC29xLg)(void* key, void** reinteropException);
  public: static ::DotNet::System::String GetString(const ::DotNet::System::String& key);
  private: static void (*CallSetString_eMSjpsyKrCDpoy__674Qaew)(void* key, void* value, void** reinteropException);
  public: static void SetString(const ::DotNet::System::String& key, const ::DotNet::System::String& value);
  private: static void (*CallDeleteKey_4Oa4KGDR__vvaosUsC29xLg)(void* key, void** reinteropException);
  public: static void DeleteKey(const ::DotNet::System::String& key);
};

} // namespace DotNet::UnityEditor


