#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumMetadataComponentType.h>
#include <DotNet/CesiumForUnity/CesiumUintVec3.h>

namespace DotNet::CesiumForUnity {
struct CesiumUintVec3;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintMat3x3;
}

namespace DotNet::CesiumForUnity {

struct CesiumUintMat3x3 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_Y4SfatHSU__2N_SCzuuF_Fg)(const ::DotNet::CesiumForUnity::CesiumUintVec3* v0, const ::DotNet::CesiumForUnity::CesiumUintVec3* v1, const ::DotNet::CesiumForUnity::CesiumUintVec3* v2, ::DotNet::CesiumForUnity::CesiumUintMat3x3* pReturnValue, void** reinteropException);
  public: static CesiumUintMat3x3 Construct(const ::DotNet::CesiumForUnity::CesiumUintVec3& v0, const ::DotNet::CesiumForUnity::CesiumUintVec3& v1, const ::DotNet::CesiumForUnity::CesiumUintVec3& v2);
  private: static void (*Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumUintMat3x3* thiz, ::std::int32_t index, ::DotNet::CesiumForUnity::CesiumUintVec3* pReturnValue, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumUintVec3 operator[](::std::int32_t index) const;
  public: ::DotNet::CesiumForUnity::CesiumMetadataComponentType componentType;
  public: ::DotNet::CesiumForUnity::CesiumUintVec3 c0;
  public: ::DotNet::CesiumForUnity::CesiumUintVec3 c1;
  public: ::DotNet::CesiumForUnity::CesiumUintVec3 c2;
};

} // namespace DotNet::CesiumForUnity


