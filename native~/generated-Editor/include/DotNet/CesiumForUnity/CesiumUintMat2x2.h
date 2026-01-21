#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumMetadataComponentType.h>
#include <DotNet/CesiumForUnity/CesiumUintVec2.h>

namespace DotNet::CesiumForUnity {
struct CesiumUintVec2;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintMat2x2;
}

namespace DotNet::CesiumForUnity {

struct CesiumUintMat2x2 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct__GL6rL0hCqqkoxAtnbIobQ)(const ::DotNet::CesiumForUnity::CesiumUintVec2* v0, const ::DotNet::CesiumForUnity::CesiumUintVec2* v1, ::DotNet::CesiumForUnity::CesiumUintMat2x2* pReturnValue, void** reinteropException);
  public: static CesiumUintMat2x2 Construct(const ::DotNet::CesiumForUnity::CesiumUintVec2& v0, const ::DotNet::CesiumForUnity::CesiumUintVec2& v1);
  private: static void (*Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumUintMat2x2* thiz, ::std::int32_t index, ::DotNet::CesiumForUnity::CesiumUintVec2* pReturnValue, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumUintVec2 operator[](::std::int32_t index) const;
  public: ::DotNet::CesiumForUnity::CesiumMetadataComponentType componentType;
  public: ::DotNet::CesiumForUnity::CesiumUintVec2 c0;
  public: ::DotNet::CesiumForUnity::CesiumUintVec2 c1;
};

} // namespace DotNet::CesiumForUnity


