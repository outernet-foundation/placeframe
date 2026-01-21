#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::UnityEngine {
struct Quaternion;
}
namespace DotNet::UnityEngine {
struct Vector3;
}

namespace DotNet::UnityEngine {

struct Quaternion {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::UnityEngine::Quaternion* pReturnValue, void** reinteropException);
  public: static Quaternion Construct();
  private: static void (*CallLookRotation_7YsCImhRrFIh_6hqa__5IAQ)(const ::DotNet::UnityEngine::Vector3* forward, const ::DotNet::UnityEngine::Vector3* upwards, ::DotNet::UnityEngine::Quaternion* pReturnValue, void** reinteropException);
  public: static ::DotNet::UnityEngine::Quaternion LookRotation(const ::DotNet::UnityEngine::Vector3& forward, const ::DotNet::UnityEngine::Vector3& upwards);
  public: float x;
  public: float y;
  public: float z;
  public: float w;
};

} // namespace DotNet::UnityEngine


