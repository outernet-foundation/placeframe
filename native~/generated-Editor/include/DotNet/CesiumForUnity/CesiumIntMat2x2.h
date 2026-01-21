#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumMetadataComponentType.h>
#include <DotNet/CesiumForUnity/CesiumIntVec2.h>

namespace DotNet::CesiumForUnity {
struct CesiumIntVec2;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntMat2x2;
}

namespace DotNet::CesiumForUnity {

struct CesiumIntMat2x2 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_FoRlw9gqeGSV1ZBPJBNk9g)(const ::DotNet::CesiumForUnity::CesiumIntVec2* v0, const ::DotNet::CesiumForUnity::CesiumIntVec2* v1, ::DotNet::CesiumForUnity::CesiumIntMat2x2* pReturnValue, void** reinteropException);
  public: static CesiumIntMat2x2 Construct(const ::DotNet::CesiumForUnity::CesiumIntVec2& v0, const ::DotNet::CesiumForUnity::CesiumIntVec2& v1);
  private: static void (*Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumIntMat2x2* thiz, ::std::int32_t index, ::DotNet::CesiumForUnity::CesiumIntVec2* pReturnValue, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumIntVec2 operator[](::std::int32_t index) const;
  public: ::DotNet::CesiumForUnity::CesiumMetadataComponentType componentType;
  public: ::DotNet::CesiumForUnity::CesiumIntVec2 c0;
  public: ::DotNet::CesiumForUnity::CesiumIntVec2 c1;
};

} // namespace DotNet::CesiumForUnity


