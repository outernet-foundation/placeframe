#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumMetadataComponentType.h>

namespace DotNet::CesiumForUnity {
struct CesiumIntVec3;
}

namespace DotNet::CesiumForUnity {

struct CesiumIntVec3 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_luE9S3oIPaPU1lLegMPAPA)(::std::int8_t x, ::std::int8_t y, ::std::int8_t z, ::DotNet::CesiumForUnity::CesiumIntVec3* pReturnValue, void** reinteropException);
  public: static CesiumIntVec3 Construct(::std::int8_t x, ::std::int8_t y, ::std::int8_t z);
  private: static void (*Construct_cAgWTHR8SgDZQ7UniQULbg)(::std::int16_t x, ::std::int16_t y, ::std::int16_t z, ::DotNet::CesiumForUnity::CesiumIntVec3* pReturnValue, void** reinteropException);
  public: static CesiumIntVec3 Construct(::std::int16_t x, ::std::int16_t y, ::std::int16_t z);
  private: static void (*Construct_2lzDmp63Mfw__oFMy0HdgWw)(::std::int32_t x, ::std::int32_t y, ::std::int32_t z, ::DotNet::CesiumForUnity::CesiumIntVec3* pReturnValue, void** reinteropException);
  public: static CesiumIntVec3 Construct(::std::int32_t x, ::std::int32_t y, ::std::int32_t z);
  private: static void (*Construct_8bShh4o97BtgzpoxMAXY5g)(::std::int64_t x, ::std::int64_t y, ::std::int64_t z, ::DotNet::CesiumForUnity::CesiumIntVec3* pReturnValue, void** reinteropException);
  public: static CesiumIntVec3 Construct(::std::int64_t x, ::std::int64_t y, ::std::int64_t z);
  private: static ::std::int64_t (*Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumIntVec3* thiz, ::std::int32_t index, void** reinteropException);
  public: ::std::int64_t operator[](::std::int32_t index) const;
  public: ::DotNet::CesiumForUnity::CesiumMetadataComponentType componentType;
  public: ::std::int64_t x;
  public: ::std::int64_t y;
  public: ::std::int64_t z;
};

} // namespace DotNet::CesiumForUnity


