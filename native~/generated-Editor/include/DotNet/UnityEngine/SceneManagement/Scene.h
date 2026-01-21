#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::UnityEngine {
class GameObject;
}
namespace DotNet::System {
template <typename T0> class Array1;
}

namespace DotNet::UnityEngine::SceneManagement {

struct Scene {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void* (*CallGetRootGameObjects_1B2M2Y8AsgTpgAmY7PhCfg)(const ::DotNet::UnityEngine::SceneManagement::Scene* thiz, void** reinteropException);
  public: ::DotNet::System::Array1<::DotNet::UnityEngine::GameObject> GetRootGameObjects() const;
  private: ::std::int32_t m_Handle;
};

} // namespace DotNet::UnityEngine::SceneManagement


