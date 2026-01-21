#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/UnityEngine/Vector3.h>
#include <DotNet/UnityEngine/Vector2.h>

namespace DotNet::UnityEngine {
struct RaycastHit;
}
namespace DotNet::UnityEngine {
class Transform;
}
namespace DotNet::UnityEngine {
struct Vector3;
}

namespace DotNet::UnityEngine {

struct RaycastHit {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::UnityEngine::RaycastHit* pReturnValue, void** reinteropException);
  public: static RaycastHit Construct();
  private: static void* (*Property_get_transform)(const ::DotNet::UnityEngine::RaycastHit* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Transform transform() const;
  private: static ::std::int32_t (*Property_get_triangleIndex)(const ::DotNet::UnityEngine::RaycastHit* thiz, void** reinteropException);
  public: ::std::int32_t triangleIndex() const;
  private: static void (*Property_get_point)(const ::DotNet::UnityEngine::RaycastHit* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Vector3 point() const;
  private: static void (*Property_set_point)(const ::DotNet::UnityEngine::RaycastHit* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException);
  public: void point(const ::DotNet::UnityEngine::Vector3& value) const;
  private: ::DotNet::UnityEngine::Vector3 m_Point;
  private: ::DotNet::UnityEngine::Vector3 m_Normal;
  private: ::std::uint32_t m_FaceID;
  private: float m_Distance;
  private: ::DotNet::UnityEngine::Vector2 m_UV;
  private: ::std::int32_t m_Collider;
};

} // namespace DotNet::UnityEngine


