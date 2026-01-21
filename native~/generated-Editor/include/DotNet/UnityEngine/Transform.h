#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::UnityEngine {
class Component;
}
namespace DotNet::UnityEngine {
class Object;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::UnityEngine {
struct Vector3;
}
namespace DotNet::UnityEngine {
class Transform;
}
namespace DotNet::UnityEngine {
struct Quaternion;
}
namespace DotNet::UnityEngine {
struct Matrix4x4;
}
namespace DotNet::System {
class String;
}
namespace DotNet::UnityEngine {
class GameObject;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::UnityEngine {

class Transform {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Transform(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Transform(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::UnityEngine::Component() const;
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static void (*Property_get_up)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Vector3 up() const;
  private: static void (*Property_set_up)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException);
  public: void up(const ::DotNet::UnityEngine::Vector3& value) const;
  private: static void (*Property_get_forward)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Vector3 forward() const;
  private: static void (*Property_set_forward)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException);
  public: void forward(const ::DotNet::UnityEngine::Vector3& value) const;
  private: static void (*Property_get_position)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Vector3 position() const;
  private: static void (*Property_set_position)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException);
  public: void position(const ::DotNet::UnityEngine::Vector3& value) const;
  private: static void* (*Property_get_parent)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Transform parent() const;
  private: static void (*Property_set_parent)(void* thiz, void* value, void** reinteropException);
  public: void parent(const ::DotNet::UnityEngine::Transform& value) const;
  private: static void (*Property_get_rotation)(void* thiz, ::DotNet::UnityEngine::Quaternion* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Quaternion rotation() const;
  private: static void (*Property_set_rotation)(void* thiz, const ::DotNet::UnityEngine::Quaternion* value, void** reinteropException);
  public: void rotation(const ::DotNet::UnityEngine::Quaternion& value) const;
  private: static void (*Property_get_localPosition)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Vector3 localPosition() const;
  private: static void (*Property_set_localPosition)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException);
  public: void localPosition(const ::DotNet::UnityEngine::Vector3& value) const;
  private: static void (*Property_get_localRotation)(void* thiz, ::DotNet::UnityEngine::Quaternion* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Quaternion localRotation() const;
  private: static void (*Property_set_localRotation)(void* thiz, const ::DotNet::UnityEngine::Quaternion* value, void** reinteropException);
  public: void localRotation(const ::DotNet::UnityEngine::Quaternion& value) const;
  private: static void (*Property_get_localScale)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Vector3 localScale() const;
  private: static void (*Property_set_localScale)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException);
  public: void localScale(const ::DotNet::UnityEngine::Vector3& value) const;
  private: static void* (*Property_get_root)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Transform root() const;
  private: static void (*Property_get_localToWorldMatrix)(void* thiz, ::DotNet::UnityEngine::Matrix4x4* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Matrix4x4 localToWorldMatrix() const;
  private: static void (*Property_get_worldToLocalMatrix)(void* thiz, ::DotNet::UnityEngine::Matrix4x4* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Matrix4x4 worldToLocalMatrix() const;
  private: static ::std::int32_t (*Property_get_childCount)(void* thiz, void** reinteropException);
  public: ::std::int32_t childCount() const;
  private: static void (*CallSetParent_hgOrrPUZTaGMovRxlX__YuA)(void* thiz, void* parent, ::std::uint8_t worldPositionStays, void** reinteropException);
  public: void SetParent(const ::DotNet::UnityEngine::Transform& parent, bool worldPositionStays) const;
  private: static void (*CallSetPositionAndRotation_4iSLIQZf65unfXZMWTVccw)(void* thiz, const ::DotNet::UnityEngine::Vector3* position, const ::DotNet::UnityEngine::Quaternion* rotation, void** reinteropException);
  public: void SetPositionAndRotation(const ::DotNet::UnityEngine::Vector3& position, const ::DotNet::UnityEngine::Quaternion& rotation) const;
  private: static ::std::int32_t (*CallGetSiblingIndex_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetSiblingIndex() const;
  private: static void* (*CallFind_huUPHg6iWoosrHfTvsoHeg)(void* thiz, void* n, void** reinteropException);
  public: ::DotNet::UnityEngine::Transform Find(const ::DotNet::System::String& n) const;
  private: static void* (*CallGetChild_7IHapUgMd7RT8__gH__cKUrw)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::UnityEngine::Transform GetChild(::std::int32_t index) const;
  private: static void (*CallDetachChildren_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void DetachChildren() const;
  private: static void* (*Property_get_gameObject)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::GameObject gameObject() const;
  private: static void* (*Property_get_transform)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Transform transform() const;
  public: template <typename T>
  T GetComponent() const;
  private: static void* (*CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException);
  private: static void* (*Property_get_name)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String name() const;
  private: static void (*Property_set_name)(void* thiz, void* value, void** reinteropException);
  public: void name(const ::DotNet::System::String& value) const;
  private: static ::std::uint32_t (*Property_get_hideFlags)(void* thiz, void** reinteropException);
  public: ::flags::flags<::DotNet::UnityEngine::HideFlags> hideFlags() const;
  private: static void (*Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const;
  private: static ::std::uint8_t (*Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator==(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator==(const Transform& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const Transform& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
};

} // namespace DotNet::UnityEngine


