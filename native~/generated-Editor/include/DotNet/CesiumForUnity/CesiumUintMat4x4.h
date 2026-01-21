#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumMetadataComponentType.h>
#include <DotNet/CesiumForUnity/CesiumUintVec4.h>

namespace DotNet::CesiumForUnity {
struct CesiumUintVec4;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintMat4x4;
}

namespace DotNet::CesiumForUnity {

struct CesiumUintMat4x4 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_UoXJ1ZrrVKjTtIO7sqwAHQ)(const ::DotNet::CesiumForUnity::CesiumUintVec4* v0, const ::DotNet::CesiumForUnity::CesiumUintVec4* v1, const ::DotNet::CesiumForUnity::CesiumUintVec4* v2, const ::DotNet::CesiumForUnity::CesiumUintVec4* v3, ::DotNet::CesiumForUnity::CesiumUintMat4x4* pReturnValue, void** reinteropException);
  public: static CesiumUintMat4x4 Construct(const ::DotNet::CesiumForUnity::CesiumUintVec4& v0, const ::DotNet::CesiumForUnity::CesiumUintVec4& v1, const ::DotNet::CesiumForUnity::CesiumUintVec4& v2, const ::DotNet::CesiumForUnity::CesiumUintVec4& v3);
  private: static void (*Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumUintMat4x4* thiz, ::std::int32_t index, ::DotNet::CesiumForUnity::CesiumUintVec4* pReturnValue, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumUintVec4 operator[](::std::int32_t index) const;
  public: ::DotNet::CesiumForUnity::CesiumMetadataComponentType componentType;
  public: ::DotNet::CesiumForUnity::CesiumUintVec4 c0;
  public: ::DotNet::CesiumForUnity::CesiumUintVec4 c1;
  public: ::DotNet::CesiumForUnity::CesiumUintVec4 c2;
  public: ::DotNet::CesiumForUnity::CesiumUintVec4 c3;
};

} // namespace DotNet::CesiumForUnity


