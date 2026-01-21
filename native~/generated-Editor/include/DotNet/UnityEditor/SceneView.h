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
namespace DotNet::UnityEditor {
class EditorWindow;
}
namespace DotNet::UnityEngine {
class Object;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::UnityEditor {
class SceneView;
}
namespace DotNet::UnityEngine {
struct Vector3;
}
namespace DotNet::UnityEngine {
struct Quaternion;
}
namespace DotNet::UnityEngine {
class Camera;
}
namespace DotNet::System {
class String;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::UnityEditor {

class SceneView {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit SceneView(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: SceneView(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::UnityEditor::EditorWindow() const;
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_lastActiveSceneView)(void** reinteropException);
  public: static ::DotNet::UnityEditor::SceneView lastActiveSceneView();
  private: static void (*Property_get_pivot)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Vector3 pivot() const;
  private: static void (*Property_set_pivot)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException);
  public: void pivot(const ::DotNet::UnityEngine::Vector3& value) const;
  private: static void (*Property_get_rotation)(void* thiz, ::DotNet::UnityEngine::Quaternion* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Quaternion rotation() const;
  private: static void (*Property_set_rotation)(void* thiz, const ::DotNet::UnityEngine::Quaternion* value, void** reinteropException);
  public: void rotation(const ::DotNet::UnityEngine::Quaternion& value) const;
  private: static void* (*Property_get_camera)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Camera camera() const;
  private: static void (*CallClose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void Close() const;
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
  public: bool operator==(const SceneView& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const SceneView& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
};

} // namespace DotNet::UnityEditor


