#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct int2;
}

namespace DotNet::Unity::Mathematics {

struct int2 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_CSSfw_WOk6__K5__v8pO4eLw)(::std::int32_t x, ::std::int32_t y, ::DotNet::Unity::Mathematics::int2* pReturnValue, void** reinteropException);
  public: static int2 Construct(::std::int32_t x, ::std::int32_t y);
  public: ::std::int32_t x;
  public: ::std::int32_t y;
};

} // namespace DotNet::Unity::Mathematics


