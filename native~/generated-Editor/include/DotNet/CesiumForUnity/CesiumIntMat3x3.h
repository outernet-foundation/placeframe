#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumMetadataComponentType.h>
#include <DotNet/CesiumForUnity/CesiumIntVec3.h>

namespace DotNet::CesiumForUnity {
struct CesiumIntVec3;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntMat3x3;
}

namespace DotNet::CesiumForUnity {

struct CesiumIntMat3x3 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_tv5P8Gb7SQuNjwU2Vh0zRw)(const ::DotNet::CesiumForUnity::CesiumIntVec3* v0, const ::DotNet::CesiumForUnity::CesiumIntVec3* v1, const ::DotNet::CesiumForUnity::CesiumIntVec3* v2, ::DotNet::CesiumForUnity::CesiumIntMat3x3* pReturnValue, void** reinteropException);
  public: static CesiumIntMat3x3 Construct(const ::DotNet::CesiumForUnity::CesiumIntVec3& v0, const ::DotNet::CesiumForUnity::CesiumIntVec3& v1, const ::DotNet::CesiumForUnity::CesiumIntVec3& v2);
  private: static void (*Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumIntMat3x3* thiz, ::std::int32_t index, ::DotNet::CesiumForUnity::CesiumIntVec3* pReturnValue, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumIntVec3 operator[](::std::int32_t index) const;
  public: ::DotNet::CesiumForUnity::CesiumMetadataComponentType componentType;
  public: ::DotNet::CesiumForUnity::CesiumIntVec3 c0;
  public: ::DotNet::CesiumForUnity::CesiumIntVec3 c1;
  public: ::DotNet::CesiumForUnity::CesiumIntVec3 c2;
};

} // namespace DotNet::CesiumForUnity


