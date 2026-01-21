#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumMetadataComponentType.h>

namespace DotNet::CesiumForUnity {
struct CesiumIntVec4;
}

namespace DotNet::CesiumForUnity {

struct CesiumIntVec4 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct__tGDX2UJ5ZtAXl4__zRN6Rg)(::std::int8_t x, ::std::int8_t y, ::std::int8_t z, ::std::int8_t w, ::DotNet::CesiumForUnity::CesiumIntVec4* pReturnValue, void** reinteropException);
  public: static CesiumIntVec4 Construct(::std::int8_t x, ::std::int8_t y, ::std::int8_t z, ::std::int8_t w);
  private: static void (*Construct_yhJRKUizUTWOe_SY6NdeKQ)(::std::int16_t x, ::std::int16_t y, ::std::int16_t z, ::std::int16_t w, ::DotNet::CesiumForUnity::CesiumIntVec4* pReturnValue, void** reinteropException);
  public: static CesiumIntVec4 Construct(::std::int16_t x, ::std::int16_t y, ::std::int16_t z, ::std::int16_t w);
  private: static void (*Construct_ima1GH0lko9R2DnR_aRPyw)(::std::int32_t x, ::std::int32_t y, ::std::int32_t z, ::std::int32_t w, ::DotNet::CesiumForUnity::CesiumIntVec4* pReturnValue, void** reinteropException);
  public: static CesiumIntVec4 Construct(::std::int32_t x, ::std::int32_t y, ::std::int32_t z, ::std::int32_t w);
  private: static void (*Construct_KoW6Dv__2RVyEhBpX4dwRww)(::std::int64_t x, ::std::int64_t y, ::std::int64_t z, ::std::int64_t w, ::DotNet::CesiumForUnity::CesiumIntVec4* pReturnValue, void** reinteropException);
  public: static CesiumIntVec4 Construct(::std::int64_t x, ::std::int64_t y, ::std::int64_t z, ::std::int64_t w);
  private: static ::std::int64_t (*Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumIntVec4* thiz, ::std::int32_t index, void** reinteropException);
  public: ::std::int64_t operator[](::std::int32_t index) const;
  public: ::DotNet::CesiumForUnity::CesiumMetadataComponentType componentType;
  public: ::std::int64_t x;
  public: ::std::int64_t y;
  public: ::std::int64_t z;
  public: ::std::int64_t w;
};

} // namespace DotNet::CesiumForUnity


