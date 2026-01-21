#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::UnityEngine {
struct Vector3;
}

namespace DotNet::UnityEngine {

struct Matrix4x4 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*CallMultiplyPoint3x4_nRoP5wpLbrdr_ZZudXtbFA)(const ::DotNet::UnityEngine::Matrix4x4* thiz, const ::DotNet::UnityEngine::Vector3* point, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Vector3 MultiplyPoint3x4(const ::DotNet::UnityEngine::Vector3& point) const;
  public: float m00;
  public: float m10;
  public: float m20;
  public: float m30;
  public: float m01;
  public: float m11;
  public: float m21;
  public: float m31;
  public: float m02;
  public: float m12;
  public: float m22;
  public: float m32;
  public: float m03;
  public: float m13;
  public: float m23;
  public: float m33;
};

} // namespace DotNet::UnityEngine


