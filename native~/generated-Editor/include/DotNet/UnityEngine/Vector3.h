#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::UnityEngine {
struct Vector3;
}

namespace DotNet::UnityEngine {

struct Vector3 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  public: static Vector3 Construct();
  private: static void (*Construct_LB__scTJntm1swre2IwXuIw)(float x, float y, float z, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  public: static Vector3 Construct(float x, float y, float z);
  private: static void (*Property_get_forward)(::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  public: static ::DotNet::UnityEngine::Vector3 forward();
  private: static void (*Property_get_up)(::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  public: static ::DotNet::UnityEngine::Vector3 up();
  private: static void (*Property_get_zero)(::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  public: static ::DotNet::UnityEngine::Vector3 zero();
  public: float x;
  public: float y;
  public: float z;
};

} // namespace DotNet::UnityEngine


