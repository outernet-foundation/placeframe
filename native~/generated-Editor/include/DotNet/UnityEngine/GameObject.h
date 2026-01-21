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
namespace DotNet::System {
class String;
}
namespace DotNet::UnityEngine {
class Object;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::UnityEngine {
class Transform;
}
namespace DotNet::System {
template <typename T0> class Array1;
}
namespace DotNet::UnityEngine {
class GameObject;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::UnityEngine {

class GameObject {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit GameObject(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: GameObject(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_wfPSjxsETIcebv8un8PGZw)(void* name, void** reinteropException);
  public: GameObject(const ::DotNet::System::String& name);
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: GameObject();
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint8_t (*Property_get_activeInHierarchy)(void* thiz, void** reinteropException);
  public: bool activeInHierarchy() const;
  private: static ::std::int32_t (*Property_get_layer)(void* thiz, void** reinteropException);
  public: ::std::int32_t layer() const;
  private: static void (*Property_set_layer)(void* thiz, ::std::int32_t value, void** reinteropException);
  public: void layer(::std::int32_t value) const;
  private: static void* (*Property_get_transform)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Transform transform() const;
  public: template <typename T>
  T GetComponent() const;
  private: static void* (*CallGetComponent_0EgxpGTzCG1YTfWqwgLniw)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_BAtcoWNWVoAVplmna6OgsQ)(void* thiz, void** reinteropException);
  public: template <typename T>
  T AddComponent() const;
  private: static void* (*CallAddComponent_0EgxpGTzCG1YTfWqwgLniw)(void* thiz, void** reinteropException);
  private: static void* (*CallAddComponent_BAtcoWNWVoAVplmna6OgsQ)(void* thiz, void** reinteropException);
  public: template <typename T>
  ::DotNet::System::Array1<T> GetComponents() const;
  private: static void* (*CallGetComponents_H1UZCBm__Pf6NnqpE7xQ8NQ)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponents_BAtcoWNWVoAVplmna6OgsQ)(void* thiz, void** reinteropException);
  private: static void (*CallSetActive_5DHWh79LLGX72UsSrgy12Q)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void SetActive(bool value) const;
  private: static void* (*CallAddComponent_NF_PuZoAY7qn_PtfB0gOuA)(void* thiz, void** reinteropException);
  private: static void* (*CallAddComponent_PYIqvoB6xIJFucZLpuXW4g)(void* thiz, void** reinteropException);
  private: static void* (*CallAddComponent_9Dl3F62kv4jRdRrSCaAhWg)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_PYIqvoB6xIJFucZLpuXW4g)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_NF_PuZoAY7qn_PtfB0gOuA)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_H1UZCBm__Pf6NnqpE7xQ8NQ)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_xszYH1Pc7IFeB_VsZOpLAg)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_h3Dg1fHhPAsIOJVZ_EBQ0Q)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_D9Lae__zo_r27FE__dPPON_Q)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_zSXCS__EpLjNvbypxgiLwTw)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_ceANxxBRdEpPcfCIAtIDbw)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_xv03rkZpw_Znk_k8us1wKw)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_6Whoj_6qM2__sUah3I8fbaA)(void* thiz, void** reinteropException);
  private: static void* (*CallAddComponent_cgILpkZPip9MNREZc7j5sA)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_cgILpkZPip9MNREZc7j5sA)(void* thiz, void** reinteropException);
  public: template <typename T>
  T GetComponentInParent() const;
  private: static void* (*CallGetComponentInParent_cgILpkZPip9MNREZc7j5sA)(void* thiz, void** reinteropException);
  private: static void* (*CallAddComponent_bqVePTBqqV2QqVo4ESth7Q)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_bqVePTBqqV2QqVo4ESth7Q)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponentInParent_bqVePTBqqV2QqVo4ESth7Q)(void* thiz, void** reinteropException);
  private: static void* (*CallFindGameObjectsWithTag_X3GzO_w9lbBwSL5__E4yHEA)(void* tag, void** reinteropException);
  public: static ::DotNet::System::Array1<::DotNet::UnityEngine::GameObject> FindGameObjectsWithTag(const ::DotNet::System::String& tag);
  private: static void* (*CallAddComponent_jKezPd1C5klHWmgOl3TpSg)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_z_rdtaHehbYFGG7_o6BG8A)(void* thiz, void** reinteropException);
  public: template <typename T>
  ::DotNet::System::Array1<T> GetComponentsInChildren() const;
  private: static void* (*CallGetComponentsInChildren_z_rdtaHehbYFGG7_o6BG8A)(void* thiz, void** reinteropException);
  public: template <typename T>
  ::DotNet::System::Array1<T> GetComponentsInChildren(bool includeInactive) const;
  private: static void* (*CallGetComponentsInChildren_STJODArO5i8B0kejx7otTA)(void* thiz, ::std::uint8_t includeInactive, void** reinteropException);
  private: static void* (*CallGetComponentsInChildren_0EgxpGTzCG1YTfWqwgLniw)(void* thiz, void** reinteropException);
  private: static void* (*CallAddComponent_z_rdtaHehbYFGG7_o6BG8A)(void* thiz, void** reinteropException);
  public: template <typename T>
  ::DotNet::System::Array1<T> GetComponentsInParent() const;
  private: static void* (*CallGetComponentsInParent_5cYXJenC2831by5N6skAPw)(void* thiz, void** reinteropException);
  private: static void* (*CallAddComponent_NuZsWWrRz5eMwjHbcVsVwA)(void* thiz, void** reinteropException);
  private: static void* (*CallAddComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException);
  private: static void* (*CallAddComponent_kHO1FlHzBtTx__KiumABg0g)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_kHO1FlHzBtTx__KiumABg0g)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_a430lQ0omIr32Y9qAs_Zdw)(void* thiz, void** reinteropException);
  private: static void* (*CallGetComponent_Is4miIX63ogCDpU56JfOjw)(void* thiz, void** reinteropException);
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
  public: bool operator==(const GameObject& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const GameObject& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
};

} // namespace DotNet::UnityEngine


