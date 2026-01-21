#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::CesiumForUnity {
enum class QuickAddItemType;
}
namespace DotNet::System {
class String;
}
namespace DotNet::System {
class Object;
}

namespace DotNet::CesiumForUnity {

class QuickAddItem {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit QuickAddItem(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: QuickAddItem(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: QuickAddItem();
  private: static void* (*Construct_MigqS33KRbgyAt6uiJjTGw)(::std::uint32_t type, void* name, void* tooltip, void* tilesetName, ::std::int64_t tilesetId, void* overlayName, ::std::int64_t overlayId, void** reinteropException);
  public: QuickAddItem(::DotNet::CesiumForUnity::QuickAddItemType type, const ::DotNet::System::String& name, const ::DotNet::System::String& tooltip, const ::DotNet::System::String& tilesetName, ::std::int64_t tilesetId, const ::DotNet::System::String& overlayName, ::std::int64_t overlayId);
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint32_t (*Field_get_type)(void* thiz, void** reinteropException);
  private: static void (*Field_set_type)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: ::DotNet::CesiumForUnity::QuickAddItemType type() const;
  public: void type(::DotNet::CesiumForUnity::QuickAddItemType value) const;
  private: static void* (*Field_get_name)(void* thiz, void** reinteropException);
  private: static void (*Field_set_name)(void* thiz, void* value, void** reinteropException);
  public: ::DotNet::System::String name() const;
  public: void name(const ::DotNet::System::String& value) const;
  private: static void* (*Field_get_tooltip)(void* thiz, void** reinteropException);
  private: static void (*Field_set_tooltip)(void* thiz, void* value, void** reinteropException);
  public: ::DotNet::System::String tooltip() const;
  public: void tooltip(const ::DotNet::System::String& value) const;
  private: static void* (*Field_get_tilesetName)(void* thiz, void** reinteropException);
  private: static void (*Field_set_tilesetName)(void* thiz, void* value, void** reinteropException);
  public: ::DotNet::System::String tilesetName() const;
  public: void tilesetName(const ::DotNet::System::String& value) const;
  private: static ::std::int64_t (*Field_get_tilesetId)(void* thiz, void** reinteropException);
  private: static void (*Field_set_tilesetId)(void* thiz, ::std::int64_t value, void** reinteropException);
  public: ::std::int64_t tilesetId() const;
  public: void tilesetId(::std::int64_t value) const;
  private: static void* (*Field_get_overlayName)(void* thiz, void** reinteropException);
  private: static void (*Field_set_overlayName)(void* thiz, void* value, void** reinteropException);
  public: ::DotNet::System::String overlayName() const;
  public: void overlayName(const ::DotNet::System::String& value) const;
  private: static ::std::int64_t (*Field_get_overlayId)(void* thiz, void** reinteropException);
  private: static void (*Field_set_overlayId)(void* thiz, ::std::int64_t value, void** reinteropException);
  public: ::std::int64_t overlayId() const;
  public: void overlayId(::std::int64_t value) const;
};

} // namespace DotNet::CesiumForUnity


