#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumMetadataComponentType.h>

namespace DotNet::CesiumForUnity {
struct CesiumIntVec2;
}

namespace DotNet::CesiumForUnity {

struct CesiumIntVec2 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_iC__gCkOnQfbe6NMbdvLiGg)(::std::int8_t x, ::std::int8_t y, ::DotNet::CesiumForUnity::CesiumIntVec2* pReturnValue, void** reinteropException);
  public: static CesiumIntVec2 Construct(::std::int8_t x, ::std::int8_t y);
  private: static void (*Construct_dZv0kAenH9__iFQ8xBVdqfQ)(::std::int16_t x, ::std::int16_t y, ::DotNet::CesiumForUnity::CesiumIntVec2* pReturnValue, void** reinteropException);
  public: static CesiumIntVec2 Construct(::std::int16_t x, ::std::int16_t y);
  private: static void (*Construct_CSSfw_WOk6__K5__v8pO4eLw)(::std::int32_t x, ::std::int32_t y, ::DotNet::CesiumForUnity::CesiumIntVec2* pReturnValue, void** reinteropException);
  public: static CesiumIntVec2 Construct(::std::int32_t x, ::std::int32_t y);
  private: static void (*Construct_tS0EQwQ6_Z2EVvmR2x05Hg)(::std::int64_t x, ::std::int64_t y, ::DotNet::CesiumForUnity::CesiumIntVec2* pReturnValue, void** reinteropException);
  public: static CesiumIntVec2 Construct(::std::int64_t x, ::std::int64_t y);
  private: static ::std::int64_t (*Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumIntVec2* thiz, ::std::int32_t index, void** reinteropException);
  public: ::std::int64_t operator[](::std::int32_t index) const;
  public: ::DotNet::CesiumForUnity::CesiumMetadataComponentType componentType;
  public: ::std::int64_t x;
  public: ::std::int64_t y;
};

} // namespace DotNet::CesiumForUnity


